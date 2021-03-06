from __future__ import print_function
import argparse
import subprocess
import json
import os


class JSONGeneratorCLI:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("-f", "--reports-per-second", type=int, default=1, dest="freq",
                                 help="Frequency of reporting each entity.")
        self.parser.add_argument("-n", "--number-of-entities", type=int, default=10, dest="number_of_entities",
                                 help="Overall number of entities this generator maintain.")
        self.parser.add_argument("-b", "--brokers", type=str, default="kafka.kafka:9092", dest="brokers")
        self.parser.add_argument("-s", "--source-name", type=str, default="source1", dest="source_name")
        self.parser.add_argument("-d", "--debug-lvl", type=str, default="INFO", dest="debug_lvl")
        self.parser.add_argument("-c", "--clear-all", type=bool, default=False, dest="to_clear")
        self.parser.add_argument("-t", "--only-create", type=bool, default=True, dest="to_only_create")
        self.parser.add_argument("-w", "--wait-for-kafka-sync", type=bool, default=False, dest="kafka_sync",
                                 help="If on, will write and await to kafka")
        self.parser.add_argument("--kube-to-file", type=str, default="NOTVALID", dest="to_file")
        self.parser.add_argument("--kube-settings", type=str, default="NOTVALID", dest="kube_settings")
        self.parser.add_argument("--kube-template", type=str, default="NOTVALID", dest="template_path",
                                 help="Path to template generator yaml")
        self.parser.add_argument("--kube-run", type=bool, default=False, dest="run",
                                 help="Run using kubectl")

    def get_user_settings(self):
        return self.parser.parse_args()


def create_command_args(settings):
    args = ["-f", settings.freq,
            "-n", settings.number_of_entities,
            "-b", settings.brokers,
            "-s", settings.source_name,
            "-d", settings.debug_lvl,
            "-t", settings.to_only_create,
            "-w", settings.kafka_sync]
    return args


if __name__ == "__main__":
    cli = JSONGeneratorCLI()
    user_settings = cli.get_user_settings()

    kube_settings_json = None
    if user_settings.template_path is not "NOTVALID":
        with open(user_settings.template_path, 'r') as template_file:
            template = template_file.read()
            kube_settings_json = json.loads(template)
    else:
        print ("You must enter --kube-template flag")
        exit()

    # Change application name
    app_name = "rand-" + user_settings.source_name
    kube_settings_json["metadata"]["name"] = app_name
    kube_settings_json["spec"]["template"]["metadata"]["name"] = app_name
    kube_settings_json["spec"]["template"]["metadata"]["labels"]["app"] = app_name
    kube_settings_json["spec"]["template"]["spec"]["containers"][0]["name"] = app_name

    # Change generator args
    generator_args = ["/usr/local/src/DetectionGenerator-master/DetectionGenerator/__main__.py"] + \
                     create_command_args(user_settings)

    if user_settings.to_file is not "NOTVALID":
        with open(user_settings.to_file, 'w') as target_file:
            print(json.dumps(kube_settings_json), file=target_file)

    if user_settings.run:
        kube_settings = user_settings.kube_settings
        if user_settings.kube_settings == "NOTVALID":
            kube_settings = os.environ.get("KUBECTL_ARGS")
        if kube_settings is not None:
            kube = subprocess.Popen(["kubectl", str(kube_settings), "create", "-f -"],
                                    stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                                    stderr=subprocess.STDOUT)
            kube.communicate(input=str(kube_settings_json))
        else:
            kube = subprocess.Popen(["kubectl", "create", "-f -"], stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                                    stderr=subprocess.STDOUT)
            kube.communicate(input=str(kube_settings_json))

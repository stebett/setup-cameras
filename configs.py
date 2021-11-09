import json

class Configs:
    """A class to store configuration file and ensure right formatting"""
    def __init__(self, config_path):
        self.config_path = config_path
        self.read_configs()

        self.pwm = self.configs["pwm"]
        self.general = self.configs["general"]
        self.properties = self.configs["properties"]
        self.dict_to_list()



    def read_configs(self):
        """Read the configuration file"""
        with open(self.config_path) as json_file:
            self.configs = json.load(json_file)

    def dict_to_list(self):
        """Create a list from the dict of configs in order to display them"""
        pwm_keys = self.pwm.keys()
        pwm_values = [self.pwm[k] for k in pwm_keys]

        general_keys = self.general.keys()
        general_values = [self.general[k] for k in general_keys]

        properties_keys = self.properties.keys()
        properties_values = [self.properties[k] for k in properties_keys]

        pwm_len = len(pwm_keys)
        general_len = len(general_keys)
        properties_len = len(properties_keys)
        list_len = pwm_len + general_len + properties_len

        self.indexes = [i for i in range(list_len)]
        self.modified = [False for _ in range(list_len)]
        self.keys = list(pwm_keys) + list(general_keys) + list(properties_keys)
        self.values = list(pwm_values) + list(general_values) + list(properties_values)
        self.parent = ["pwm" for _ in range(pwm_len)] + \
                      ["general" for _ in range(general_len)] + \
                      ["properties" for _ in range(properties_len)]

    def list_to_dict(self):
        """Push changes made on the list to the dict"""
        for parent, value, key in zip(self.parent, self.values, self.keys):
            self.configs[parent][key] = value

    def save(self, filename):
        """Save the dictionary as a json file"""
        with open(filename, 'w') as f:
            json.dump(self.configs, f, indent=4)


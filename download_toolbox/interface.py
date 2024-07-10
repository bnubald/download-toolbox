import logging
import os

import orjson

from download_toolbox.location import Location
from download_toolbox.time import Frequency


class DataSetFactory(object):
    @classmethod
    def get_item(cls, impl):
        import download_toolbox.data
        klass_name = DataSetFactory.get_klass_name(impl)

        if hasattr(download_toolbox.data, klass_name):
            return getattr(download_toolbox.data, klass_name)

        logging.error("No class named {0} found in download_toolbox.data".format(klass_name))
        raise ReferenceError

    @classmethod
    def get_klass_name(cls, name):
        return name.split(":")[-1]


def get_dataset_config_implementation(config: os.PathLike):
    if not str(config).endswith(".json"):
        raise RuntimeError("{} does not look like a JSON configuration".format(config))
    if not os.path.exists(config):
        raise RuntimeError("{} is not a configuration in existence".format(config))

    logging.debug("Retrieving implementations details from {}".format(config))

    with open(config) as fh:
        data = fh.read()

    cfg = orjson.loads(data)
    logging.debug("Loaded configuration {}".format(cfg))
    cfg, implementation = cfg["data"], cfg["implementation"]

    # TODO: Getting a nicer implementation might be the way forward, but this will do
    #  with the Frequency naively matching given that they're fully caps-locked strings
    location = Location(**cfg["_location"])
    freq_dict = {k.strip("_"): getattr(Frequency, v) for k, v in cfg.items() if v in list(Frequency.__members__)}
    remaining = {k.strip("_"): v
                 for k, v in cfg.items()
                 if k not in [*["_{}".format(el) for el in freq_dict.keys()], "_location"]}

    create_kwargs = dict(location=location, **remaining, **freq_dict)
    logging.info("Attempting to instantiate {} with loaded configuration".format(implementation))
    logging.debug("Converted kwargs from the retrieved configuration: {}".format(create_kwargs))

    return DataSetFactory.get_item(implementation)(**create_kwargs)
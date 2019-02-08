""" Circuits module of Bosch thermostat. """
from .const import (GET, SUBMIT, NAME, PATH, OPERATION_MODE,
                    HC_SETPOINT_ROOMTEMPERATURE, HC_MANUAL_ROOMSETPOINT,
                    HC_TEMPORARY_TEMPERATURE)
from .helper import crawl, BoschEntities, BoschSingleEntity


class Circuits(BoschEntities):
    """
    Circuits main object containing multiple Circuit objects.
    """
    def __init__(self, requests, circuit_type):
        """
        :param dict requests: { GET: get function, SUBMIT: submit function}
        :param str circuit_type: is it HC or DHW
        """
        self._circuit_type = circuit_type
        super().__init__(requests)

    @property
    def circuits(self):
        """ Get circuits. """
        return self.get_items()

    async def initialize(self, circuits=None):
        """ Initialize HeatingCircuits asynchronously. """
        restoring_data = True
        if not circuits:
            circuits = await self.retrieve_from_module(1, self._circuit_type)
            restoring_data = False
        for circuit in circuits:
            if "references" in circuit:
                circuit_object = Circuit(
                    self._requests,
                    circuit['id'],
                    restoring_data
                    )
                circuit_object.add_data(circuit['id'], circuit['references'])
                if not restoring_data:
                    await circuit_object.initialize()
                    circuit['references'] = circuit_object.json_scheme
                self._items.append(circuit_object)


class Circuit(BoschSingleEntity):
    """ Single Circuit object. """

    def __init__(self, requests, attr_id, restoring_data):
        """
        :param dict requests: { GET: get function, SUBMIT: submit function}
        :param str name: name of heating circuit.

        """
        self._requests = requests
        self._circuits_path = {}
        self._operation_list = []
        self._references = None
        self._restoring_data = restoring_data
        super().__init__(attr_id.split('/').pop(), attr_id, restoring_data, {})

    def add_data(self, path, references):
        self._main_data[PATH] = path
        for key in references:
            if self._restoring_data:
                short_id = key
                self._circuits_path[short_id] = references[key]
            else:
                short_id = key['id'].split('/').pop()
                self._circuits_path[short_id] = key["id"]
            self._data[short_id] = None

    @property
    def json_scheme(self):
        return self._circuits_path

    async def update(self):
        """ Update info about Circuit asynchronously. """
        for key in self._data:
            result = await self._requests[GET](
                self._circuits_path[key])
            self._data[key] = (result['value'] if 'value' in result
                               else self._data[key])
            if key == OPERATION_MODE:
                self._operation_list = result['allowedValues']

    async def update_requested_keys(self, key):
        """ Update info about Circuit asynchronously. """
        if key in self._data:
            result = await self._requests[GET](
                self._circuits_path[key])
            self._data[key] = (result['value'] if 'value' in result
                               else self._data[key])
            if key == OPERATION_MODE:
                self._operation_list = result['allowedValues']

    async def initialize(self):
        """ Check each uri if return json with values. """
        keys_to_del = []
        for key, value in self._circuits_path.items():
            result_id = await crawl(value, [], 1, self._requests[GET])
            if not result_id:
                keys_to_del.append(key)
        for key in keys_to_del:
            del self._data[key]
            del self._circuits_path[key]
        self._json_scheme_ready = True
        print("sprawdzam co ja tu mam")
        print(self.name)
        print(self._data)
        print(self._circuits_path)
        print("KONIC")

    @property
    def allowed_operations(self):
        return self._operation_list

    async def set_mode(self, new_mode):
        """ Set mode of Circuit. """
        if new_mode in self._operation_list:
            await self._requests[SUBMIT](
                self._circuits_path[OPERATION_MODE],
                new_mode)

    async def set_temperature(self, temperature):
        """ Set temperature of Circuit. """
        await self._requests[SUBMIT](
            self._circuits_path[HC_TEMPORARY_TEMPERATURE],
            temperature)

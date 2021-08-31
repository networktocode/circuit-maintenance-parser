"""Definition of Processor class."""
import logging
import traceback
import itertools

from typing import Iterable, Type, Dict, List

from pydantic import BaseModel, Extra
from pydantic.error_wrappers import ValidationError

from circuit_maintenance_parser.output import Maintenance
from circuit_maintenance_parser.data import NotificationData
from circuit_maintenance_parser.parser import Parser
from circuit_maintenance_parser.errors import ParsingError, ProcessorError, ProviderError


logger = logging.getLogger(__name__)


class GenericProcessor(BaseModel, extra=Extra.forbid):
    """Base class for the Processors."""

    # data_parsers contain the Parser Classes that will be tried
    data_parsers: List[Type[Parser]]

    # extended_data is custom default data from a Provider used to complement data from parsing
    extended_data: Dict = {}

    # maintenances_data is the variable that contains the result of the processor
    maintenances_data: List = []

    def process(self, data: NotificationData, extended_data: Dict) -> Iterable[Maintenance]:
        """Using the data_parsers, with a custom logic, will try to generate one or more Maintenances."""
        self.extended_data = extended_data

        data_part_and_parser_combinations = [
            (data_part, data_parser)
            for (data_part, data_parser) in itertools.product(data.get_data_parts(), self.data_parsers)
            if data_part.type in data_parser.get_data_types()
        ]

        if not data_part_and_parser_combinations:
            error_message = (
                f"None of the supported parsers for processor {self.__class__.__name__} ("
                f"{', '.join([data_parser.__name__ for data_parser in self.data_parsers])}) was matching any of the "
                f"provided data types ({', '.join([data_part.type for data_part in data.get_data_parts()])})."
            )

            logger.debug(error_message)
            # TODO: fix the __cause__ error
            raise ProcessorError(error_message)

        for data_part, data_parser in data_part_and_parser_combinations:
            try:
                self._process_hook(data_parser().parse(data_part.content))

            except (ParsingError, ValidationError) as exc:

                error_message = (
                    f"Parser class {data_parser.__name__} from {self.__class__.__name__} was not successful."
                )
                logger.debug(error_message + "\n" + traceback.format_exc())
                raise ProcessorError(error_message) from exc

        self._post_process_hook()

        return self.maintenances_data

    def _process_hook(self, maintenances_extracted_data: List):
        """Custom method per processor to accumulate the data from each DataPart."""
        raise NotImplementedError

    def _post_process_hook(self):
        """Hook to add a post parsing process logic."""

    def _extend_processor_data(self, current_maintenance_data):
        """Method used to extend Maintenance data with some defaults."""
        current_maintenance_data["organizer"] = (
            self.extended_data.get("organizer")
            if "organizer" not in current_maintenance_data or current_maintenance_data["organizer"] == "None"
            else current_maintenance_data.get("organizer")
        )

        if "provider" not in current_maintenance_data:
            current_maintenance_data["provider"] = self.extended_data.get("provider")


class SimpleProcessor(GenericProcessor):
    """Processor to get all the Maintenance Data in each Data Part."""

    def _process_hook(self, maintenances_extracted_data):
        """For each data extracted (that can be multiple), we try to build a complete Maintenance."""
        for extracted_data in maintenances_extracted_data:
            self._extend_processor_data(extracted_data)
            self.maintenances_data.append(Maintenance(**extracted_data))


class CombinedProcessor(GenericProcessor):
    """Processor for parse multiple DataParts to get a Maintenance notification."""

    # The CombinedProcessor will consolidate all the parsed data into this variable
    combined_maintenance_data: Dict = {}

    def _process_hook(self, maintenances_extracted_data):
        """All the parsers contribute with a subset of data that is extended."""
        # We only expect one data object from these parsers
        if len(maintenances_extracted_data) == 1:
            self.combined_maintenance_data = {
                **self.combined_maintenance_data,
                **maintenances_extracted_data[0],
            }
        else:
            raise ParsingError(f"Unexpected data retrieved from parser: {maintenances_extracted_data}")

    def _post_process_hook(self):
        """After processing all the parsers, we try to combine all the data together."""
        self._extend_processor_data(self.combined_maintenance_data)
        try:
            self.maintenances_data.append(Maintenance(**self.combined_maintenance_data))
        except ValidationError as exc:
            raise ProviderError("Not enough information available to create a Maintenance notification.") from exc

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
    """Base class for the Processors.

    Attributes:
        data_parsers: List of `Parsers` that will be used to parse the data when the data type matches. Each `Parser`
            will return a dictionary with extracted data, and depending on the logic, this will be used to create and
            return `Maintenances`
        extended_data (Optional): Dictionary containing information to complement the data extracted by the `Parsers`
            that is coming from the `Provider`
    """

    data_parsers: List[Type[Parser]]
    extended_data: Dict = {}

    def process(self, data: NotificationData, extended_data: Dict) -> Iterable[Maintenance]:
        """Using the data_parsers, with a custom logic, will try to generate one or more Maintenances."""
        self.extended_data = extended_data
        maintenances_data: List = []
        # First, we generate a list of tuples with a `DataPart` and `Parser` if the data type from the first is
        # supported by the second.
        data_part_and_parser_combinations = [
            (data_part, data_parser)
            for (data_part, data_parser) in itertools.product(data.data_parts, self.data_parsers)
            if data_part.type in data_parser.get_data_types()
        ]

        if not data_part_and_parser_combinations:
            error_message = (
                f"None of the supported parsers for processor {self.__class__.__name__} ("
                f"{', '.join([data_parser.__name__ for data_parser in self.data_parsers])}) was matching any of the "
                f"provided data types ({', '.join([data_part.type for data_part in data.data_parts])})."
            )

            logger.debug(error_message)
            # TODO: fix the __cause__ error
            raise ProcessorError(error_message)

        for data_part, data_parser in data_part_and_parser_combinations:
            try:
                self.process_hook(data_parser().parse(data_part.content), maintenances_data)

            except (ParsingError, ValidationError) as exc:
                error_message = "Parser class %s from %s was not successful.\n%s"
                logger.debug(error_message, data_parser.__name__, self.__class__.__name__, traceback.format_exc())
                raise ProcessorError from exc

        self.post_process_hook(maintenances_data)

        return maintenances_data

    def process_hook(self, maintenances_extracted_data: List, maintenances_data: List):
        """Custom method per processor to accumulate the data from each DataPart."""
        raise NotImplementedError

    def post_process_hook(self, maintenances_data: List):
        """Hook to add a post parsing process logic."""

    def extend_processor_data(self, current_maintenance_data):
        """Method used to extend Maintenance data with some defaults."""
        current_maintenance_data["organizer"] = (
            self.extended_data.get("organizer")
            if "organizer" not in current_maintenance_data
            else current_maintenance_data.get("organizer")
        )

        if "provider" not in current_maintenance_data:
            current_maintenance_data["provider"] = self.extended_data.get("provider")


class SimpleProcessor(GenericProcessor):
    """Processor to get all the Maintenance Data in each Data Part."""

    def process_hook(self, maintenances_extracted_data, maintenances_data):
        """For each data extracted (that can be multiple), we try to build a complete Maintenance."""
        for extracted_data in maintenances_extracted_data:
            self.extend_processor_data(extracted_data)
            maintenances_data.append(Maintenance(**extracted_data))


class CombinedProcessor(GenericProcessor):
    """Processor that combines the parsed output of multiple DataParts to get a single unified Maintenance notification."""

    # The CombinedProcessor will consolidate all the parsed data into this variable
    combined_maintenance_data: Dict = {}

    def process_hook(self, maintenances_extracted_data, maintenances_data):
        """All the parsers contribute with a subset of data that is extended."""
        # We only expect one data object from these parsers
        if len(maintenances_extracted_data) == 1:
            self.combined_maintenance_data.update(maintenances_extracted_data[0])
        else:
            raise ProcessorError(f"Unexpected data retrieved from parser: {maintenances_extracted_data}")

    def post_process_hook(self, maintenances_data):
        """After processing all the parsers, we try to combine all the data together."""
        self.extend_processor_data(self.combined_maintenance_data)
        try:
            maintenances_data.append(Maintenance(**self.combined_maintenance_data))
        except ValidationError as exc:
            raise ProviderError("Not enough information available to create a Maintenance notification.") from exc

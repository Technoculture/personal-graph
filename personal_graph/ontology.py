import logging
import owlready2  # type: ignore
from owlready2 import OwlReadyOntologyParsingError


def from_rdf(file_path: str) -> owlready2.namespace.Ontology:
    """
    Load an ontology from a specified file path.

    @param file_path: Path to the ontology file

    @return: owlready2.namespace.Ontology: The loaded ontology

    @raise: OwlReadyOntologyParsingError: Unable to parse the specified file
    """
    try:
        onto = owlready2.get_ontology(file_path).load()  # Loading the rdf file
        logging.info(onto)
        return onto

    except OwlReadyOntologyParsingError as err:
        raise OwlReadyOntologyParsingError(
            f"Error loading ontology: {str(err)}"
        ) from err

    except FileNotFoundError as ferr:
        raise FileNotFoundError(f"File not found: {str(ferr)}") from ferr

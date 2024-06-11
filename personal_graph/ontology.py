import logging
import owlready2  # type: ignore


def from_rdf(file_path: str) -> owlready2.namespace.Ontology:
    """
    This method will load an ontology.
    @param file_path: path to ontology file
    @return: Ontology
    """

    onto = owlready2.get_ontology(file_path).load()  # Loading the rdf file

    logging.info(onto)
    return onto

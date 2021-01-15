import os

from export.abstract_exporter import AExporter


class Dot(AExporter):
    """ A simple Dot Exporter using igraph """

    def start_up(self, **kwargs):
        # Here wer simply create the folder if it does not exist
        self.out_folder = kwargs["export_output_folder"]
        if not os.path.exists(self.out_folder):
            os.makedirs(self.out_folder)

    def export(self, prot_graph):
        accession = prot_graph.vs["accession"][0]
        prot_graph.write_dot(os.path.join(self.out_folder, accession + ".dot"))

    def tear_down(self):
        # We do not need to tear down a graph export to dot files
        pass
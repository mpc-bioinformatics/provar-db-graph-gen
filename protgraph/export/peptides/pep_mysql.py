import mysql.connector

from protgraph.export.peptides.abstract_peptide_exporter import \
    APeptideExporter


class PepMySQL(APeptideExporter):
    """
    A MySQL - Exporter to export PEPTIDES
    into the peptides table

    Those tables will contain all output generated by
    each of the processes. Keep in mind that this table can
    be extremely large, depending on the parmeters set in this tool.

    NOTE: Maybe even exceeding trillion of results for one protein!
    """

    @property
    def skip_x(self) -> bool:
        return self.get_skip_x

    @property
    def peptide_min_length(self) -> int:
        return self.get_peptide_min_length

    @property
    def max_miscleavages(self) -> int:
        return self.get_miscleavages

    @property
    def use_igraph(self) -> bool:
        return self.get_use_igraph

    @property
    def peptide_max_length(self) -> int:
        return self.get_peptide_length

    @property
    def batch_size(self) -> int:
        return self.get_batch_size

    def start_up(self, **kwargs):
        # Here we generate a connection to mysql
        # and generate the corresponding tables

        # Connection and other parameters
        self.host = kwargs["pep_mysql_host"]  # Host
        self.port = kwargs["pep_mysql_port"]  # Port
        self.user = kwargs["pep_mysql_user"]  # User
        self.password = kwargs["pep_mysql_password"]  # Password
        self.database = kwargs["pep_mysql_database"]  # Database
        self.no_duplicates = kwargs["pep_mysql_no_duplicates"]

        # Traversal parameters:
        self.get_peptide_length = kwargs["pep_mysql_hops"]  # Number of hops. E.G. 2: s -> h_1 -> h_2 -> e
        self.get_miscleavages = kwargs["pep_mysql_miscleavages"]  # A filter criterion how many miscleavages?
        self.get_peptide_min_length = kwargs["pep_mysql_min_pep_length"]  # Peptide minimum length
        self.get_skip_x = kwargs["pep_mysql_skip_x"]
        self.get_use_igraph = kwargs["pep_mysql_use_igraph"]
        self.get_batch_size = 10000  # TODO do this as a Parameter!

        # Initialize connection
        try:
            self.conn = mysql.connector.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                database=self.database,
                port=self.port
            )
            # Set a cursor
            self.cursor = self.conn.cursor()
        except Exception as e:
            raise Exception("Could not establish a connection to MySQL (Peptides).", e)

        # Create tables if they not exist
        try:
            self._create_tables(**kwargs)
        except Exception as e:
            raise Exception("Could not create tables in MySQL (Peptides).", e)

    def _create_tables(self, **kwargs):
        """ Create the accessions and peptides tables """
        try:
            # create accessions, so that we only save numbers in the large table!
            cur = self.conn.cursor()
            cur.execute("""
                create table if not exists accessions (
                    id INT NOT NULL AUTO_INCREMENT,
                    accession VARCHAR(15) CHARACTER SET ascii NOT NULL,
                    PRIMARY KEY(id)
                );""")
        except Exception as e:
            print("Error creating accessions table. Continuing... (Reason: {})".format(str(e)))
        finally:
            self.conn.commit()
            cur.close()

        try:
            # Create the large peptides table containing most information
            cur = self.conn.cursor()
            cur.execute("""
            CREATE TABLE  if not exists peptides (
                id BIGINT UNIQUE AUTO_INCREMENT,
                weight {0} NOT NULL,
                a_count SMALLINT NOT NULL,
                b_count SMALLINT NOT NULL,
                c_count SMALLINT NOT NULL,
                d_count SMALLINT NOT NULL,
                e_count SMALLINT NOT NULL,
                f_count SMALLINT NOT NULL,
                g_count SMALLINT NOT NULL,
                h_count SMALLINT NOT NULL,
                i_count SMALLINT NOT NULL,
                j_count SMALLINT NOT NULL,
                k_count SMALLINT NOT NULL,
                l_count SMALLINT NOT NULL,
                m_count SMALLINT NOT NULL,
                n_count SMALLINT NOT NULL,
                o_count SMALLINT NOT NULL,
                p_count SMALLINT NOT NULL,
                q_count SMALLINT NOT NULL,
                r_count SMALLINT NOT NULL,
                s_count SMALLINT NOT NULL,
                t_count SMALLINT NOT NULL,
                u_count SMALLINT NOT NULL,
                v_count SMALLINT NOT NULL,
                w_count SMALLINT NOT NULL,
                x_count SMALLINT NOT NULL,  -- NOT SKIPPED
                y_count SMALLINT NOT NULL,
                z_count SMALLINT NOT NULL,
                n_terminus VARCHAR(1) CHARACTER SET ascii NOT NULL,
                c_terminus VARCHAR(1) CHARACTER SET ascii NOT NULL,
                PRIMARY KEY ({1}));""".format(
                "BIGINT" if kwargs["mass_dict_type"] is int else "DOUBLE",
                """id""" if self.no_duplicates else "id"
                ))
        except Exception as e:
            print("Error createing peptides table. Continuing... (Reason: {})".format(str(e)))
        finally:
            self.conn.commit()
            cur.close()
            self.peptides_keys = [
                "weight",
                "a_count", "b_count", "c_count", "d_count", "e_count", "f_count", "g_count", "h_count",
                "i_count", "j_count", "k_count", "l_count", "m_count", "n_count", "o_count", "p_count",
                "q_count", "r_count", "s_count", "t_count", "u_count", "v_count", "w_count", "x_count",
                "y_count", "z_count", "n_terminus", "c_terminus"
            ]
        # TODO DL create Index for select statement! only if no duplicates
        try:
            cur = self.conn.cursor()
            cur.execute("CREATE INDEX peptide_idx ON peptides ({})".format(",".join(self.peptides_keys)))
        except Exception as e:
            print("Error createing peptides index. Continuing... (Reason: {})".format(str(e)))
        finally:
            self.conn.commit()
            cur.close()

        try:
            # Create the peptides meta information (can also be extremely large)
            cur = self.conn.cursor()
            cur.execute("""
            CREATE TABLE  if not exists peptides_meta (
                id BIGINT AUTO_INCREMENT,
                peptides_id BIGINT,
                accession_id INT,
                path MEDIUMTEXT CHARACTER SET ascii NOT NULL,
                miscleavages INT NOT NULL,
                PRIMARY KEY (id)
            );""")  # References to peptide and accession removed for performance reasons
        except Exception as e:
            print("Error createing peptides_meta table. Continuing... (Reason: {})".format(str(e)))
        finally:
            self.conn.commit()
            cur.close()
            self.peptides_meta_keys = [
                "peptides_id",
                "accession_id",
                "path",
                "miscleavages"
            ]

        # Set insert statement for peptides
        self.statement_accession = "INSERT INTO accessions(accession) VALUES (%s);"

        self.statement_peptides_select = "SELECT id from peptides where " \
            + " and ".join([x + "=" + y for x, y in zip(self.peptides_keys, ["%s"]*len(self.peptides_keys))])

        self.statement_peptides_insert_no_dup = "INSERT INTO peptides (" \
            + ",".join(self.peptides_keys) \
            + ") SELECT " \
            + ",".join(["%s"]*len(self.peptides_keys)) \
            + " WHERE NOT EXISTS( " + self.statement_peptides_select + ") LIMIT 1 "

        self.statement_peptides = "INSERT INTO peptides (" \
            + ",".join(self.peptides_keys) \
            + ") VALUES (" \
            + ",".join(["%s"]*len(self.peptides_keys)) \
            + ")"

        self.statement_meta_peptides = "INSERT INTO peptides_meta (" \
            + ",".join(self.peptides_meta_keys) \
            + ") VALUES (" \
            + ",".join(["%s"]*len(self.peptides_meta_keys)) \
            + ")"

    def export(self, prot_graph, queue):
        # First insert accession into accession table and retrieve its id:
        # since we only do this per protein!
        accession = prot_graph.vs[0]["accession"]
        self.cursor.execute(
            self.statement_accession,
            (accession,)
        )
        self.accession_id = self.cursor.lastrowid

        # Then we continue with the export function
        super().export(prot_graph, queue)

        # and commit everything in the conenction for a protein
        self.conn.commit()

    def export_peptides(self, prot_graph, l_path_nodes, l_path_edges, l_peptide, l_miscleavages, _):
        for a, b, c, d in zip(l_path_nodes, l_path_edges, l_peptide, l_miscleavages):
            self.export_peptide(prot_graph, a, b, c, d)

    def export_peptide(self, prot_graph, path_nodes, path_edges, peptide, miscleavages):
        # Get the weight
        if "mono_weight" in prot_graph.es[path_edges[0]].attributes():
            weight = sum(prot_graph.es[path_edges]["mono_weight"])
        else:
            weight = -1

        # Set the output tuple
        peptides_tup = (
            weight,
            # Counts of Aminoacids
            peptide.count("A"), peptide.count("B"), peptide.count("C"), peptide.count("D"), peptide.count("E"),
            peptide.count("F"), peptide.count("G"), peptide.count("H"), peptide.count("I"), peptide.count("J"),
            peptide.count("K"), peptide.count("L"), peptide.count("M"), peptide.count("N"), peptide.count("O"),
            peptide.count("P"), peptide.count("Q"), peptide.count("R"), peptide.count("S"), peptide.count("T"),
            peptide.count("U"), peptide.count("V"), peptide.count("W"), peptide.count("X"), peptide.count("Y"),
            peptide.count("Z"),
            # N and C Terminus
            peptide[0], peptide[-1]
        )

        # Insert new entry into database:
        if self.no_duplicates:
            # If no dupicates, we search for a duplicate
            self.cursor.execute(self.statement_peptides_insert_no_dup, peptides_tup*2)
            self.conn.commit()
            peptides_id = self.cursor.lastrowid
            if peptides_id < 1:
                # No entry, insert!
                try:
                    self.cursor.execute(self.statement_peptides_select, peptides_tup)
                    peptides_id = next(self.cursor)[0]
                except Exception:
                    # Skip rollback, since we can simly reexecute the statements here for the same peptide
                    self.export_peptide(prot_graph, path_nodes, path_edges, peptide, miscleavages)
                    return
        else:
            # simply insert it into the database
            self.cursor.execute(self.statement_peptides, peptides_tup)
            peptides_id = self.cursor.lastrowid

        # Insert meta data information of peptide ALWAYS
        peptides_meta_tup = (
            peptides_id,
            self.accession_id,
            ",".join(map(str, path_nodes)),
            miscleavages
        )
        self.cursor.execute(self.statement_meta_peptides, peptides_meta_tup)

    def tear_down(self):
        # Close the connection to mysql
        try:
            self.cursor.close()  # Close cursor
            self.conn.close()  # Close connection
        except Exception as e:
            print("Connection to MySQL  could not be closed. (Reason: {})".format(str(e)))

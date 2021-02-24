import psycopg2

from protgraph.export.peptides.abstract_peptide_exporter import \
    APeptideExporter


class PepPostgres(APeptideExporter):
    """
    A PostGreSQL - Exporter to export PEPTIDES
    into the peptides table

    Those tables will contain all output generated by
    each of the processes. Keep in mind that this table can
    be extremely large, depending on the parmeters set in this tool.

    NOTE: Maybe even exceeding trillion of results for one protein!
    """

    @property
    def skip_x(self) -> bool:
        return self.get_postgres_skip_x

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

    def start_up(self, **kwargs):
        # Here we generate a connection to postgres
        # and generate the corresponding tables

        # Connection and other parameters
        self.host = kwargs["pep_postgres_host"]  # Host
        self.port = kwargs["pep_postgres_port"]  # Port
        self.user = kwargs["pep_postgres_user"]  # User
        self.password = kwargs["pep_postgres_password"]  # Password
        self.database = kwargs["pep_postgres_database"]  # Database
        self.postgres_no_duplicates = kwargs["pep_postgres_no_duplicates"]

        # Traversal parameters:
        self.get_peptide_length = kwargs["pep_postgres_hops"]  # Number of hops. E.G. 2: s -> h_1 -> h_2 -> e
        self.get_miscleavages = kwargs["pep_postgres_miscleavages"]  # A filter criterion how many miscleavages?
        self.get_peptide_min_length = kwargs["pep_postgres_min_pep_length"]  # Peptide minimum length
        self.get_postgres_skip_x = kwargs["pep_postgres_skip_x"]
        self.get_use_igraph = kwargs["pep_postgres_use_igraph"]

        # Initialize connection
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                dbname=self.database
            )
            # Set a cursor
            self.cursor = self.conn.cursor()
        except Exception as e:
            raise Exception("Could not establish a connection to Postgres (Peptides).", e)

        # Create tables if they not exist
        try:
            self._create_tables(**kwargs)
        except Exception as e:
            raise Exception("Could not create tables in Postgres (Peptides).", e)

    def _create_tables(self, **kwargs):
        """ Create the accessions and peptides tables """
        try:
            # create accessions, so that we only save numbers in the large table!
            cur = self.conn.cursor()
            cur.execute("""
                create table if not exists accessions (
                    id SERIAl PRIMARY KEY,
                    accession VARCHAR(15) NOT NULL
                );""")
        except Exception as e:
            print("Error createing accessions table. Continuing... (Reason: {})".format(str(e)))
        finally:
            self.conn.commit()
            cur.close()

        try:
            # Create the large peptides table containing most information
            cur = self.conn.cursor()
            cur.execute("""
            CREATE TABLE  if not exists peptides (
                id BIGSERIAL UNIQUE,
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
                n_terminus character(1) NOT NULL,
                c_terminus character(1) NOT NULL,
                PRIMARY KEY ({1}));""".format(
                "BIGINT" if kwargs["mass_dict_type"] is int else "DOUBLE PRECISION",
                """ weight, a_count, b_count, c_count, d_count, e_count, f_count, g_count,
                h_count, i_count, j_count, k_count, l_count, m_count, n_count, o_count,
                p_count, q_count, r_count, s_count, t_count, u_count, v_count, w_count,
                x_count, y_count, z_count, n_terminus, c_terminus""" if self.postgres_no_duplicates else "id"
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
        try:
            cur = self.conn.cursor()
            cur.execute("CREATE INDEX ON peptides ({})".format(",".join(self.peptides_keys)))
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
                id BIGSERIAL,
                peptides_id BIGINT references peptides(id),
                accession_id INT references accessions(id),
                path INT[] NOT NULL,
                miscleavages INT NOT NULL,
                PRIMARY KEY (id)
            );""")
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
        self.statement_accession = "INSERT INTO accessions(accession) VALUES (%s) RETURNING id;"

        self.statement_peptides_select = "SELECT id from peptides where " \
            + " and ".join([x + "=" + y for x, y in zip(self.peptides_keys, ["%s"]*len(self.peptides_keys))])

        self.statement_peptides = "INSERT INTO peptides (" \
            + ",".join(self.peptides_keys) \
            + ") VALUES (" \
            + ",".join(["%s"]*len(self.peptides_keys)) \
            + ") returning id"

        self.statement_meta_peptides = "INSERT INTO peptides_meta (" \
            + ",".join(self.peptides_meta_keys) \
            + ") VALUES (" \
            + ",".join(["%s"]*len(self.peptides_meta_keys)) \
            + ")"

    def export(self, prot_graph):
        # First insert accession into accession table and retrieve its id:
        # since we only do this per protein!
        accession = prot_graph.vs[0]["accession"]
        self.cursor.execute(
            self.statement_accession,
            (accession,)
        )
        self.accession_id = self.cursor.fetchone()[0]

        # Then we continue with the export function
        super().export(prot_graph)

        # and commit everything in the conenction for a protein
        self.conn.commit()

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
        with self.conn.cursor() as cur:

            if self.postgres_no_duplicates:
                # If no dupicates, we search for a duplicate
                cur.execute(self.statement_peptides_select, peptides_tup)
                peptides_id_fetched = cur.fetchone()
                if peptides_id_fetched is None:
                    # No entry, insert!
                    cur.execute(self.statement_peptides, peptides_tup)
                    peptides_id_fetched = cur.fetchone()
            else:
                # simply insert it into the database
                cur.execute(self.statement_peptides, peptides_tup)
                peptides_id_fetched = cur.fetchone()
            peptides_id = peptides_id_fetched[0]

            # Inster meta data information of peptide ALWAYS
            peptides_meta_tup = (
                peptides_id,
                self.accession_id,
                path_nodes,
                miscleavages
            )
            cur.execute(self.statement_meta_peptides, peptides_meta_tup)

    def tear_down(self):
        # Close the connection to postgres
        try:
            self.cursor.close()  # Close cursor
            self.conn.close()  # Close connection
        except Exception as e:
            print("Connection to PostgreSQL  could not be closed. (Reason: {})".format(str(e)))

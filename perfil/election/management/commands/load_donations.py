from textwrap import dedent

from perfil.election.management.commands import election_keys
from perfil.election.models import Donation, Election
from perfil.utils.management.commands import ImportCsvCommand
from perfil.utils.tools import parse_date, parse_decimal, parse_document


class Command(ImportCsvCommand):

    help = dedent("""
        Import CSV generated by: https://github.com/rafapolo/tribuna

        Organize data in a MySQL database as described in the instructions and
        then export a CSV with:

            SELECT *
            FROM doacoes
            WHERE tipo = "candidato"
            INTO OUTFILE '/path/to/some/dir/doacoes.csv'
            FIELDS TERMINATED BY ','
            ENCLOSED BY '"'
            LINES TERMINATED BY '\';

        You might have to add the following settings to your my.cnf:

            [mysqld]
            secure_file_priv=""

            [client]
            loose-local-infile=1
    """)

    to_cache = (Election, election_keys),
    model = Donation
    bulk_size = 2 ** 10
    headers = (
        'id',
        'uf',
        'partido',
        'cargo',
        'candidato',
        'numero',
        'ano',
        'cpf_candidato',
        'doador_original',
        'doador',
        'cpf_doador',
        'cpf_doador_original',
        'recurso',
        'setor_economico',
        'data',
        'motivo',
        'fonte',
        'valor',
        'valor_at',
        'tipo'
    )

    def serialize(self, reader):
        for line in reader:
            for key, value in line.items():
                if value == '\\N':  # MySQL default for NULL values as string
                    line[key] = None

            election_id = self.cache.get(election_keys(line))
            if not election_id:
                yield None
                continue

            yield Donation(
                election_id=election_id,
                donator=line['doador'],
                donator_id=parse_document(line['cpf_doador']),
                original_donator=line['doador_original'],
                original_donator_id=parse_document(line['cpf_doador_original']),
                date=parse_date(line['data']),
                value=parse_decimal(line['valor']),
                description=line['recurso']
            )

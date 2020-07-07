import pandas as pd
import database
from io import StringIO
import re

# Make PostgreSQL Connection
engine = database.get_database()
con = engine.raw_connection()


def query(command):
    df_models = pd.read_sql(command, con=con)
    buf = StringIO()
    df_models.to_json(buf, orient='records')
    return buf.getvalue()


def conflict_paths(paths, new_added_path):
    conflict_paths_set = set()
    new_path_regex = re.sub('<(\w+)>', "\\\w+", new_added_path)
    for path in paths:
        if re.match(new_path_regex, path):
            conflict_paths_set.add(path)
        elif re.match(re.sub('<(\w+)>', "\\\w+", path), new_added_path):
            conflict_paths_set.add(path)
    return conflict_paths_set


def get_query(path_query_map, path):
    for key in path_query_map:
        p = re.compile(r'<\w+>')
        wildcards = p.findall(key)
        path_group_regex = key
        for wildcard in wildcards:
            path_group_regex = path_group_regex.replace(wildcard, "(?P{wildcard}\w+)".format(wildcard=wildcard))
        if re.match(path_group_regex, path):
            query = path_query_map[key]
            matches = re.search(path_group_regex, path)
            for wildcard in wildcards:
                group_value = matches.group(wildcard[1:-1])
                query = query.replace(wildcard, group_value)
            return query

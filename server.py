from flask import Flask,request
from query import query as query_command,get_query,conflict_paths
import json
app= Flask(__name__)

path_query_map={}

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/query', methods=['GET', 'POST'])
def query():
    return app.response_class(
        response=query_command(request.json['query']),
        status=200,
        mimetype='application/json'
    )

@app.route('/register')
def register():
    conflict_paths_set = conflict_paths(path_query_map.keys(),request.json['path'])
    if not conflict_paths_set:
        path_query_map[request.json['path']]=request.json['query']
        return 'ok'
    return 'conflict with path(s) '+ str(conflict_paths_set)

@app.route('/paths')
def paths():
    from io import StringIO
    buf = StringIO()
    json.dump(path_query_map,buf)
    return app.response_class(
        response=buf.getvalue(),
        status=200,
        mimetype='application/json'
    )

@app.route('/path/<path:subpath>')
def generated_path(subpath):
    return app.response_class(
        response=query_command(get_query(path_query_map,subpath)),
        status=200,
        mimetype='application/json'
    )


if __name__=='__main__':
    app.run()
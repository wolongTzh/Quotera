from flask import Flask , request, render_template, send_file, jsonify, session, redirect, url_for
import requests , json , random
import io, os
import shutil            # ← add this line
import tempfile               # ← add this

from .ttl_generator import convert_csv_to_ttl
from .ttl_parser import gen_json_from_ttl
from .ttl2tree import get_tree_json
import uuid
import tempfile
from .certify import certify



# this file lives at …/Quotera/api/index.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# point at the existing api/data folder:
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

TEMP_DIR = tempfile.gettempdir()

app = Flask(__name__)
app.secret_key = 'edukg.org'

@app.route('/certification',methods=["POST"])
def certification():
    file1 = request.files.get('file1')
    temp_dir = tempfile.gettempdir()
    random_id = str(uuid.uuid4())
    file1_path = os.path.join(temp_dir, random_id + "-entities.csv")
    file1.save(file1_path)

    name = "Zheng Tan"
    level = "level 2"
    json_path, png_path, pdf_path = certify(file1_path, name, level)
    print(json_path, png_path, pdf_path)
    return jsonify({'success': True, "json_path":json_path, "png_path":png_path, "pdf_path":pdf_path})

@app.route('/download-presonal-graph')
def download_presonal_graph():
    ttl_path = session.get('ttl_path')
    # 你可以从磁盘读取，也可以是内存生成的内容
    buffer = io.BytesIO()
    with open(ttl_path, 'rb') as f:
        buffer.write(f.read())
    buffer.seek(0)

    # 返回文件
    return send_file(
        buffer,
        as_attachment=True,
        download_name='data.ttl',  # 文件名
        mimetype='text/ttl'
    )

@app.route('/presonal-graph',methods=["POST"])
def presonal_graph():
    file1 = request.files.get('file1')
    file2 = request.files.get('file2')
    random_id = str(uuid.uuid4())


    temp_dir = tempfile.gettempdir()

    file1_path = os.path.join(temp_dir, random_id + "-entities.csv")
    file2_path = os.path.join(temp_dir, random_id + "-relations.csv")
    file3_path = os.path.join(temp_dir, random_id + "-graph.ttl")
    file1.save(file1_path)
    file2.save(file2_path)
    try:
      convert_csv_to_ttl(entities_csv_path=file1_path, relations_csv_path=file2_path, output_ttl_path=file3_path, graph_id=random_id)
    except:
      return jsonify({'success': False, 'error': str(e)}), 500
    graphs = {
        "graph": gen_json_from_ttl(file3_path)["graph"]
    }
    # print(get_tree_json(file3_path))
    treeData = {
        "graph": get_tree_json(file3_path)
    }
    os.remove(file1_path)
    os.remove(file2_path)
    # print(graphs)
    session['graphs'] = graphs
    session['treeData'] = treeData
    session['ttl_path'] = file3_path
    return jsonify({'success': True})
    # return render_template('personal-graph.html', json_data=graphs) 
    # return graphs


@app.route('/save-ttl', methods=['POST'])
def save_ttl():
    ttl_path = session.get('ttl_path')
    if not ttl_path or not os.path.exists(ttl_path):
        return jsonify({'error': 'No TTL to save'}), 400

    data = request.get_json() or {}
    raw_name = data.get('filename', '').strip()
    if not raw_name:
        return jsonify({'error': 'Filename is required'}), 400

    # sanitize and enforce .ttl
    safe_base = "".join(c for c in raw_name if c.isalnum() or c in ('-','_')).rstrip()
    filename = safe_base + ('.ttl' if not safe_base.lower().endswith('.ttl') else '')
    dest_path = os.path.join(DATA_DIR, filename)

    # ─── EXISTENCE CHECK ─────────────────────────────────
    if os.path.exists(dest_path):
        return jsonify({'error': f'A file named "{filename}" already exists.'}), 409
    # ──────────────────────────────────────────────────────

    try:
        shutil.move(ttl_path, dest_path)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # only pop once it’s truly been moved
    session.pop('ttl_path', None)
    return jsonify({'saved': True, 'filename': filename}), 200


@app.route('/discard-ttl', methods=['POST'])
def discard_ttl():
    ttl_path = session.pop('ttl_path', None)

    # delete only temp files
    if ttl_path and ttl_path.startswith(TEMP_DIR):
        try:
            os.remove(ttl_path)
        except FileNotFoundError:
            pass

    session.pop('graphs', None)
    session.pop('treeData', None)
    return jsonify({'discarded': True})


@app.route('/build-upload',methods=["GET"])
def build_upload():
    return render_template('builder-upload.html') 

@app.route('/build-guide',methods=["GET"])
def build_guide():
    return render_template('builder-guide.html')    

@app.route('/example',methods=["GET"])
def example():
    return render_template('example.html')    

@app.route('/certificate',methods=["GET"])
def certificate():
    return render_template('certificate.html')   

@app.route('/personal',methods=["GET"])
def personal():
    if 'graphs' not in session:
      return "No data found", 400
    graphs = session.get('graphs')
    treeData = session.get('treeData')
    # print(treeData)
    if not graphs:
        return "No data found", 400
    return render_template('personal-graph.html', json_data=graphs, tree_data=treeData)    
    


@app.route('/', methods=['GET'])
def home():
    """
    Landing page.  If the session still points to a *temporary* TTL file
    (one created from an upload), delete it.  If the path points inside
    DATA_DIR we leave it alone so saved graphs are never lost.
    """
    ttl_path = session.pop('ttl_path', None)

    # remove only if it’s in the OS temp directory
    if ttl_path and ttl_path.startswith(TEMP_DIR):
        try:
            os.remove(ttl_path)
        except FileNotFoundError:
            pass           # file already gone → ignore

    # clear any cached graph JSON
    session.pop('graphs',   None)
    session.pop('treeData', None)

    return render_template('index.html')


@app.route("/view-graphs", methods=["GET"])
def view_graphs():
    # ① list every .ttl file so the dropdown is populated
    files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith(".ttl"))

    # ② see if the user already picked one (?file=foo.ttl in the URL)
    filename = request.args.get("file")
    graphs = treeData = {}          # safe empty defaults
    if filename and filename in files:
        ttl_path = os.path.join(DATA_DIR, filename)
        graphs   = {"graph": gen_json_from_ttl(ttl_path)["graph"]}
        treeData = {"graph": get_tree_json(ttl_path)}

    return render_template(
        "view-graphs.html",
        files=files,
        current_file=filename,
        json_data=graphs,
        tree_data=treeData
    )




# index.py  ───────────────────────────────────────────


# ── helper: build the two JSON blobs your templates expect ───────────
def _prepare_graph_objects(ttl_path: str):
    """
    Convert a .ttl file into the dicts consumed by view-graphs.html:
        graphs   = {"graph": … }
        treeData = {"graph": … }
    """
    graphs   = {"graph": gen_json_from_ttl(ttl_path)["graph"]}
    treeData = {"graph": get_tree_json(ttl_path)}
    return graphs, treeData

@app.route('/load-graph', methods=['POST'])
def load_graph():
    """Receive a filename and redraw the viewer page *with* the picker."""
    filename = request.form.get('filename', '').strip()
    if not filename:
        return "No file selected", 400

    ttl_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(ttl_path):
        return f"{filename} not found", 404

    # build graph JSON
    graphs, treeData = _prepare_graph_objects(ttl_path)

    # stash for JS buttons (download / save / discard)
    session['graphs']   = graphs
    session['treeData'] = treeData
    session['ttl_path'] = ttl_path

    # we still need the list for the dropdown
    files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith('.ttl'))

    # ▶︎ render the SAME template that contains the picker ◀︎
    return render_template(
        'view-graphs.html',
        files=files,
        current_file=filename,
        json_data=graphs,
        tree_data=treeData
    )



if __name__ == '__main__':
    app.run(port=8081, host="0.0.0.0", debug=True)  

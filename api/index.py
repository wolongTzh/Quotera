from flask import Flask , request, render_template, send_file, jsonify, session
import requests , json , random
import io, os
from ttl_generator import convert_csv_to_ttl
from ttl_parser import gen_json_from_ttl
import uuid
import tempfile



app = Flask(__name__)
app.secret_key = 'edukg.org'

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
    graphs = gen_json_from_ttl(file3_path)["graph"]
    os.remove(file1_path)
    os.remove(file2_path)
    print("from personal")
    print(presonal_graph)
    session['graphs'] = graphs
    session['ttl_path'] = file3_path
    return jsonify({'success': True})
    # return render_template('personal-graph.html', json_data=graphs) 
    # return graphs

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
    print("from personal")
    print(graphs)
    if not graphs:
        return "No data found", 400
    return render_template('personal-graph.html', json_data=graphs)    


@app.route('/',methods=["GET"])
def home():
    # 判断ttl_path是否在session中
    if 'ttl_path' in session:
        ttl_path = session.get('ttl_path')
        if ttl_path:
            if os.path.exists(ttl_path):
                os.remove(ttl_path)
            # 删除该session中的ttl_path
            session.pop('ttl_path', None)
    if 'graphs' in session:
        graphs = session.get('graphs')
        if graphs:
            session.pop('graphs', None)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(port=8081, host="0.0.0.0", debug=True)  

from flask import Flask , request, render_template, send_file, jsonify, session
import requests , json , random
import io


app = Flask(__name__)
app.secret_key = 'edukg.org'

@app.route('/download-presonal-graph')
def download_presonal_graph():
    # 你可以从磁盘读取，也可以是内存生成的内容
    content = "id,name\n1,Alice\n2,Bob"
    buffer = io.BytesIO()
    buffer.write(content.encode('utf-8'))
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

    print(file1.filename)
    file1_path = "/home/tz/cui/Quotera/api/templates/a.csv"
    file2_path = "/home/tz/cui/Quotera/api/templates/b.csv"
    # file1.save(file1_path)
    # file2.save(file2_path)
    graphs = {
    "nodes":[
      {
        "id": "Basic programming concepts",
        "name": "Basic programming concepts",
        "type": "LPitem"
      },
      {
        "id": "Understand basic Python syntax",
        "name": "Understand basic Python syntax",
        "type": "LPitem"
      },
      {
        "id": "Introduction to Python",
        "name": "Introduction to Python",
        "type": "RIitem"
      },
      {
        "id": "List Topics",
        "name": "List Topics",
        "type": "PRitem"
      }
    ],
    "links":[
      {
        "source": "Basic programming concepts",
        "target": "Understand basic Python syntax",
        "relation": "hasChild"
      },
      {
        "source": "Introduction to Python",
        "target": "Understand basic Python syntax",
        "relation": "hasLearningPoint"
      },
      {
        "source": "List Topics",
        "target": "Introduction to Python",
        "relation": "hasResource"
      }
      ]
    }
    session['graphs'] = graphs
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
    graphs = session.get('graphs')
    if not graphs:
        return "No data found", 400
    return render_template('personal-graph.html', json_data=graphs)    


@app.route('/',methods=["GET"])
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(port=8081, host="0.0.0.0", debug=True)  

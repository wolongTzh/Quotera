from flask import Flask , request, render_template, send_file
import requests , json , random
import io


app = Flask(__name__)

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

@app.route('/presonal-graph',methods=["GET"])
def presonal_graph():
    graphs = {
    "nodes":[
      {
        "id": "Basic programming concepts",
        "name": "Basic programming concepts"
      },
      {
        "id": "Understand basic Python syntax",
        "name": "Understand basic Python syntax"
      },
      {
        "id": "Introduction to Python",
        "name": "Introduction to Python"
      },
      {
        "id": "List Topics",
        "name": "List Topics"
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
        "relation": "related leaning point"
      },
      {
        "source": "List Topics",
        "target": "Introduction to Python",
        "relation": "related resource"
      }
      ]
    }
    return render_template('personal-graph.html', json_data=graphs) 

@app.route('/build-upload',methods=["GET"])
def build_upload():
    return render_template('builder-upload.html') 

@app.route('/build-guide',methods=["GET"])
def build_guide():
    return render_template('builder-guide.html')    

@app.route('/example',methods=["GET"])
def example():
    return render_template('example.html')    


@app.route('/',methods=["GET"])
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(port=8081, host="0.0.0.0", debug=True)  

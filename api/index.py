from flask import Flask , request, render_template
import requests , json , random


app = Flask(__name__)
def select(a):
    dict ={'Anime':'a','Comic':'b','Game':'c','Literature':'d','Original':'e','Internet':'f','Other':'g','Video':'h','Poem':'i','NCM':'j','Philosophy':'k','Funny':'l'}
    if str(a) in dict.keys() :
        return dict[str(a)]
    else :
        return dict[str(random.choice(list(dict.keys())))]

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


@app.route('/search/',methods=["GET"])
def search():
    query = request.args.get("s")
    key = 'hitokoto'
    url = requests.get("https://api.pwxiao.top/sentences/i.json")
    text = url.text
    data = json.loads(text)
        
    matches = [item for item in data if key in item and query in item[key]]
    matches = json.dumps(matches,ensure_ascii=False)
    return matches
    


@app.route('/',methods=["GET"])
def return_OneText():
    return render_template('index_out.html')

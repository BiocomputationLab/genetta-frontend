import os
import shutil
import json
import time
import ast

from xml.sax._exceptions import SAXParseException
from rdflib.exceptions import ParserError
from flask import Flask
from flask import session
from flask import render_template
from flask import redirect
from flask import send_from_directory
from flask import request
from flask import url_for
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from flask_login import current_user
from flask_login import login_user
from flask_login import logout_user
from flask_login import login_required

from app.utility import forms
from app.utility import form_handlers
from app.utility.change_log.logger import ChangeLogger
from app.utility.sbol_connector.connector import SBOLConnector
from app.converter.handler import file_convert
from app.converter.sbol_convert import export
from app.graph.world_graph import WorldGraph
from app.utility.login import LoginHandler

from app.tools.graph_query.handler import GraphQueryHandler
from app.tools.visualiser.design import DesignDash
from app.tools.visualiser.editor import EditorDash
from app.tools.visualiser.cypher import CypherDash
from app.tools.visualiser.projection import ProjectionDash
from app.tools.visualiser.truth import TruthDash
from app.tools.enhancer.enhancer import Enhancer
from app.tools.kg_expansion.builder import TruthGraphBuilder
from app.tools.evaluator.evaluator import Evaluator

root_dir = "app"
static_dir = os.path.join(root_dir, "assets")
template_dir = os.path.join(root_dir, "templates")
sessions_dir = os.path.join(root_dir, "sessions")
truth_save_dir = os.path.join(root_dir, "truth_saves")
example_dir = os.path.join(static_dir, "examples")
example_file = os.path.join(static_dir, "examples","explanation.json")
user_gns = "graph_names.json"

server = Flask(__name__, static_folder=static_dir,
               template_folder=template_dir)


db_host = os.environ.get('NEO4J_HOST', 'localhost')
db_port = os.environ.get('NEO4J_PORT', '7687')
db_auth = os.environ.get('NEO4J_AUTH', "neo4j/Radeon12300")
db_auth = tuple(db_auth.split("/"))
uri = f'neo4j://{db_host}:{db_port}' 
login_graph_name = "login_manager"

logger = ChangeLogger()
graph = WorldGraph(uri,db_auth,reserved_names=[login_graph_name],logger=logger)


# Tools
design_dash = DesignDash(__name__, server, graph)
editor_dash = EditorDash(__name__, server, graph)
cypher_dash = CypherDash(__name__, server, graph)
projection_dash = ProjectionDash(__name__, server, graph)
truth_dash = TruthDash(__name__, server, graph)
tg_builder = TruthGraphBuilder(graph)
tg_query = GraphQueryHandler(graph.truth)
enhancer = Enhancer(graph)
evaluator = Evaluator(graph)


design_dash.app.enable_dev_tools(debug=True)
cypher_dash.app.enable_dev_tools(debug=True)
projection_dash.app.enable_dev_tools(debug=True)
editor_dash.app.enable_dev_tools(debug=True)
truth_dash.app.enable_dev_tools(debug=True)

app = DispatcherMiddleware(server, {
    design_dash.pathname: design_dash.app.server,
    cypher_dash.pathname: cypher_dash.app.server,
    projection_dash.pathname: projection_dash.app.server,
    editor_dash.pathname: editor_dash.app.server,
})
connector = SBOLConnector()



server.config['SESSION_PERMANENT'] = True
server.config['SESSION_TYPE'] = 'filesystem'
server.config['SESSION_FILE_THRESHOLD'] = 100
server.config['SECRET_KEY'] = "Secret"
server.config['SESSION_FILE_DIR'] = os.path.join(root_dir, "flask_sessions")
login_manager = LoginHandler(server,graph.driver,login_graph_name)
login_manager.login_view = "login"
fn_size_threshold = os.environ.get('FILESIZE_THRESHOLD', 106384)


@login_manager.user_loader
def load_user(user_name):
    if (login_manager.admin is not None and
            user_name == login_manager.admin.username):
        return login_manager.admin
    for user in login_manager.get_users():
        if user.username == user_name:
            return user
    return None


@server.route('/login', methods=['GET', 'POST'])
def login():
    create_user_form = forms.CreateUserForm()
    create_admin_form = forms.CreateAdminForm()
    if not current_user.is_authenticated:
        if login_manager.admin is None:
            if create_admin_form.validate_on_submit():
                admin = login_manager.add_admin(create_admin_form.username.data,
                                                create_admin_form.password.data)
                login_user(admin)
                if len(list(set(graph.truth.name) & set(graph.get_graph_names()))) == 0:
                    tg_builder.seed()
                return redirect(url_for('index'))
            else:
                return render_template('signup.html', create_admin_form=create_admin_form)
        if create_user_form.validate_on_submit():
            un = create_user_form.username.data
            pw = create_user_form.password.data
            user = login_manager.get_user(un, pw)
            if user is None:
                if login_manager.does_exist(un):
                    return render_template('signup.html', create_user_form=create_user_form, 
                                           invalid_username=True)
                user = login_manager.add_user(un, pw)
            login_user(user)
            next = request.args.get('next')
            return redirect(next or url_for('index'))
        else:
            return render_template('signup.html', create_user_form=create_user_form)
    next = request.args.get('next')
    return redirect(next or url_for('index'))


@server.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("index")


@server.route('/', methods=['GET', 'POST'])
@server.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    return render_template('index.html')


@server.route('/graph-admin', methods=['GET', 'POST'])
@login_required
def graph_admin():
    if not _is_admin():
        return render_template('invalid_route.html', invalid_credentials=True)
    tg_form = forms.add_truth_graph_form(truth_save_dir)
    project_names = graph.driver.project.names()
    drop_projection = forms.add_remove_projection_form(project_names)
    success_string = None
    if tg_form.validate_on_submit():
        if tg_form.tg_save.data:
            _save_truth_graph()
            success_string = f'Truth Graph Saved.'
        elif tg_form.tg_reseed.data:
            graph.truth.drop()
            tg_builder.seed()
            success_string = f'Reset Truth Graph'
        elif tg_form.tg_expand.data:
            tg_builder.expand()
            success_string = f'Expanded Truth Graph'
        elif tg_form.tg_restore.data:
            fn = os.path.join(truth_save_dir, request.form["files"])
            graph.truth.drop()
            graph.truth.load(fn)
            success_string = f'Restored Truth Graph {request.form["files"]}'
    elif drop_projection.validate_on_submit():
        dg = drop_projection.graphs.data
        if dg == "Remove All":
            for n in project_names:
                graph.driver.project.drop(n)
        else:
            graph.driver.project.drop(dg)
    return render_template('admin.html', tg_form=tg_form,
                           drop_projection=drop_projection,
                           success_string=success_string)


@server.route('/modify-graph', methods=['GET', 'POST'])
@login_required
def modify_graph():
    cf_true = forms.ConnectorFormTrue()
    cf_false = forms.ConnectorFormFalse()
    upload_graph = forms.UploadGraphForm()
    paste_graph = forms.PasteGraphForm()
    sbh_graph = forms.SynbioGraphForm()
    lg_form = forms.LargeGraphForm()
    remove_graph,export_graph = _add_graph_forms()
    add_graph_fn = None
    err_string = None
    success_string = None
    if "visual_filename" in session.keys():
        add_graph_fn = session["visual_filename"]
        g_name = session["graph_name"]
        ft = session["ft"]
    if upload_graph.validate_on_submit():
        add_graph_fn, g_name = form_handlers.handle_upload(upload_graph, session["user_dir"])
        ft = upload_graph.file_type.data
    elif paste_graph.validate_on_submit():
        add_graph_fn, g_name = form_handlers.handle_paste(paste_graph, session["user_dir"])
        ft = paste_graph.file_type.data
    elif sbh_graph.validate_on_submit():
        try:
            add_graph_fn, g_name = form_handlers.handle_synbiohub(sbh_graph, session["user_dir"], connector)
        except TypeError:
            add_graph_fn = None
        if add_graph_fn is None:
            err_string = "Unable to find record."
        ft = "sbol"
    elif remove_graph.validate_on_submit():
        gn = remove_graph.graphs.data
        graph.remove_design(gn)
        remove_graph,_ = _add_graph_forms()
        try:
            os.remove(os.path.join(session["user_dir"], gn+".xml"))
        except FileNotFoundError:
            pass
        _remove_user_gn(gn)
        success_string = f'{gn} Removed.'
    elif export_graph.validate_on_submit():
        out_dir = os.path.join(session["user_dir"], "designs")
        try:
            os.mkdir(out_dir)
        except FileExistsError:
            pass
        fn = export_graph.e_graphs.data+".xml"
        dfn = os.path.join(session["user_dir"], fn)
        export(dfn, [export_graph.e_graphs.data],logger)
        shutil.copyfile(dfn, os.path.join(out_dir, fn))
        shutil.make_archive(out_dir, 'zip', out_dir)
        shutil.rmtree(out_dir)
        return send_from_directory(session["user_dir"], "designs.zip", as_attachment=True)
    if add_graph_fn is not None:
        if g_name == "":
            g_name = add_graph_fn.split(os.path.sep)[-1].split(".")[0]
        if cf_true.cft_submit.data:
            orig_filename = add_graph_fn
            dg = connector.connect(add_graph_fn)
            add_graph_fn = orig_filename.split(
                "/")[-1].split(".")[0] + "_connected.xml"
            add_graph_fn = os.path.join(session["user_dir"], add_graph_fn)
            dg.save(add_graph_fn, "xml")
            os.remove(orig_filename)
            del session["visual_filename"]
            del session["graph_name"]
            del session["ft"]

        elif cf_false.cff_submit.data:
            add_graph_fn = session["visual_filename"]
            del session["visual_filename"]
            del session["graph_name"]
            del session["ft"]

        elif connector.can_connect(add_graph_fn):
            session["ft"] = ft
            session["visual_filename"] = add_graph_fn
            session["graph_name"] = g_name
            return render_template('modify_graph.html', upload_graph=upload_graph,
                                   paste_graph=paste_graph, sbh_graph=sbh_graph, export_graph=export_graph,
                                   remove_graph=remove_graph,cf_true=cf_true, cf_false=cf_false)

        elif not os.path.isfile(add_graph_fn):
            return render_template('modify_graph.html', upload_graph=upload_graph,
                                   paste_graph=paste_graph, sbh_graph=sbh_graph, export_graph=export_graph,
                                   remove_graph=remove_graph)

        elif os.path.getsize(add_graph_fn) > fn_size_threshold:
            if not lg_form.lg_decline.data and not lg_form.lg_confirm.data:
                session["ft"] = ft
                session["visual_filename"] = add_graph_fn
                session["graph_name"] = g_name
                return render_template('modify_graph.html', upload_graph=upload_graph,
                                   paste_graph=paste_graph, sbh_graph=sbh_graph, export_graph=export_graph,
                                   remove_graph=remove_graph,large_graph=lg_form)
            del session["visual_filename"]
            del session["graph_name"]
            del session["ft"]
            if lg_form.lg_decline.data:
                try:
                    os.remove(add_graph_fn)
                except FileNotFoundError:
                    pass
                return render_template('modify_graph.html', upload_graph=upload_graph,
                        paste_graph=paste_graph, sbh_graph=sbh_graph,
                        remove_graph=remove_graph,
                        export_graph=export_graph,
                        err_string=err_string, success_string=success_string)
            
        if g_name in graph.get_design_names():
            return render_template('modify_graph.html', upload_graph=upload_graph,
                                    paste_graph=paste_graph, sbh_graph=sbh_graph, export_graph=export_graph,
                                    remove_graph=remove_graph, err_string="Graph name is taken.")
        _add_user_gn(g_name)
        success,ret_str = _convert_file(add_graph_fn, g_name, ft)
        if success:
            success_string = ret_str
        else:
            err_string = ret_str
        remove_graph,export_graph = _add_graph_forms()
        return render_template('modify_graph.html', upload_graph=upload_graph,
                               paste_graph=paste_graph, sbh_graph=sbh_graph, export_graph=export_graph,
                               remove_graph=remove_graph, success_string=success_string,err_string=err_string)

    return render_template('modify_graph.html', upload_graph=upload_graph,
                           paste_graph=paste_graph, sbh_graph=sbh_graph,
                           remove_graph=remove_graph,
                           export_graph=export_graph,
                           err_string=err_string, success_string=success_string)

@server.route('/truth-query', methods=['GET', 'POST'])
@login_required
def truth_query():
    handlers = tg_query.get_handlers()
    query_form = forms.build_truth_query_form(handlers)
    results = None
    info_string = None
    no_results = False
    if request.method == "POST":
        if query_form.submit_query.id in request.form:
            qd = query_form.query.data
            qt = query_form.query_type.data
            results = tg_query.query(qt,qd)
            results = forms.build_tgrf(results,qt)
        else:
            for identifier,action in request.form.items():
                if (identifier == query_form.query.id or 
                    identifier == query_form.query_type.id):
                    continue
                source,result,qt = identifier.split(" - ")
                if action == "load":
                    session["cypher_entities"] = result
                    return redirect(cypher_dash.pathname)
                elif action == "positive":
                    tg_query.feedback(qt,source,result)
                    info_string = "Positive Feedback integrated."
                elif action == "negative":
                    tg_query.feedback(qt,source,result,positive=False)
                    info_string = "Negative Feedback integrated."
                else:
                    raise NotImplementedError(action)
            qd = query_form.query.data
            qt = query_form.query_type.data
            results = tg_query.query(qt,qd)
            results = forms.build_tgrf(results,qt)
        if len(results) == 0:
            no_results=True
        return render_template('truth_query.html', query_bar=query_form,
                               results=results,info_string=info_string,
                               no_results=no_results)
    return render_template('truth_query.html', query_bar=query_form)

@server.route('/visualiser', methods=['GET', 'POST'])
@login_required
def visualiser():
    return redirect(design_dash.pathname)


@server.route('/editor', methods=['GET', 'POST'])
@login_required
def editor():
    return redirect(editor_dash.pathname)


@server.route('/cypher', methods=['GET', 'POST'])
@login_required
def cypher():
    if not _is_admin():
        return render_template('invalid_route.html', invalid_credentials=True)
    return redirect(cypher_dash.pathname)


@server.route('/gds', methods=['GET', 'POST'])
@login_required
def gds():
    return redirect(projection_dash.pathname)


@server.route('/truth', methods=['GET', 'POST'])
@login_required
def truth():
    return redirect(truth_dash.pathname)


@server.route('/evaluate', methods=['GET', 'POST'])
@login_required
def evaluate():
    upload = forms.UploadDesignForm()
    gns = graph.get_design_names()
    user_d_names = _get_user_gn(gns)
    cg = forms.add_evaluate_graph_form(user_d_names)
    gn = None
    if request.method == "POST":
        if upload.validate_on_submit():
            gn, _, error = _upload_graph(upload)
            if error is not None:
                return render_template("evaluate.html",  cg=cg,error_str=error)
        elif cg.validate_on_submit():
            gn = cg.graphs.data
        if gn is not None:
            feedback = evaluator.evaluate(gn, flatten=True)
            descriptions = _get_evaluator_descriptions(feedback)
            return render_template("evaluate.html", feedback=feedback,
                                   descriptions=descriptions)

    return render_template("evaluate.html",  cg=cg)


@server.route('/canonicalise', methods=['GET', 'POST'])
@login_required
def canonicalise():
    d_names = graph.get_design_names()
    user_d_names = _get_user_gn(d_names)
    cg = forms.add_choose_graph_form(user_d_names)
    p_changes = None
    changes = None
    gn = None
    if request.method == "POST":
        if "close" in request.form:
            return render_template("canonicaliser.html", cg=cg)
        elif cg.validate_on_submit():
            rm = cg.run_mode.data
            gn = cg.graphs.data

        if gn is not None:
            if not rm:
                p_changes = enhancer.canonicalise(gn,automated=False)
            else:
                changes = enhancer.canonicalise(gn)

        if "submit_semi_canonicaliser" in request.form:
            replacements = {}
            for k, v in request.form.items():
                if k == "submit_semi_canonicaliser":
                    continue
                elif v != "none":
                    v = ast.literal_eval(v)
                    replacements[k] = v
            gn = session["c_gn"]
            changes = enhancer.apply_canonicalise(replacements, gn)
            del session["c_gn"]

        if p_changes is not None:
            if len(p_changes) == 0:
                return render_template("canonicaliser.html", cg=cg, no_match=True)
            changes = forms.add_semi_canonicaliser_form(p_changes)
            session["c_gn"] = gn
            return render_template("canonicaliser.html", cg=cg, p_changes=changes, gn=gn)
        
        if changes is not None:
            if len(changes) == 0:
                return render_template("canonicaliser.html",cg=cg, no_changes=True)
            else:
                return render_template("canonicaliser.html",  cg=cg, s_changes=changes, gn=gn)
    return render_template("canonicaliser.html",  cg=cg)


@server.route('/enhancement', methods=['GET', 'POST'])
@login_required
def enhancement():
    d_names = graph.get_design_names()
    user_d_names = _get_user_gn(d_names)
    run_e = forms.add_enhancement_form(user_d_names)
    p_changes = None
    changes = None
    gn = None
    if request.method == "POST":
        if "close" in request.form:
            return render_template("enhancement.html",  run_e=run_e)
        elif run_e.validate_on_submit():
            automate = run_e.automate.data
            gn = run_e.graphs.data
            if automate:
                changes = enhancer.enhance(gn, automated=True)
            else:
                p_changes = enhancer.enhance(gn, automated=False)
        if "submit_enhancer" in request.form:
            replacements = {}
            for k, v in request.form.items():
                if k == "submit_enhancer":
                    continue
                if v == "y":
                    enhancer_mod,old, new = k.split()
                    if enhancer_mod not in replacements:
                        replacements[enhancer_mod] = {}
                    if old in replacements[enhancer_mod]:
                        existing = replacements[enhancer_mod][old]
                        if isinstance(existing,list):
                            replacements[enhancer_mod][old].append(new)
                        else:
                            replacements[enhancer_mod][old] = [existing,
                                                               new]
                    else:
                        replacements[enhancer_mod][old] = new
            gn = session["c_gn"]
            changes = enhancer.apply_enhance(replacements, gn)
            del session["c_gn"]

        if p_changes is not None:
            if len(p_changes) == 0:
                return render_template("enhancement.html", run_e=run_e, no_changes=True)
            changes = forms.add_semi_enhancer_form(p_changes)
            session["c_gn"] = gn
            return render_template("enhancement.html", run_e=run_e, p_changes=changes, gn=gn)
        if changes is not None:
            if len(changes) == 0:
                return render_template("enhancement.html", run_e=run_e, no_changes=True)
            else:
                return render_template("enhancement.html", run_e=run_e, s_changes=changes, gn=gn)
            
    return render_template("enhancement.html",  run_e=run_e)

@server.route('/tutorial', methods=['GET', 'POST'])
def tutorial():
    return render_template('tutorial.html')

@server.route('/examples', methods=['GET', 'POST'])
def examples():
    example_design_form = forms.create_example_design_form(example_file)
    if request.method == "POST":
        ret_strs = {}
        for k,v in request.form.items():
            if k == example_design_form.submit_example.id:
                continue
            if v != "y":
                continue
            g_name = f'{current_user.get_id()} - {k.split(".")[0]}'
            _add_user_gn(g_name)
            fn = os.path.join(example_dir,k)
            if g_name in graph.get_design_names():
                ret_strs[f'{g_name}: already exists'] = False
            else:
                success,ret_str = _convert_file(fn, g_name, "SBOL")
                ret_strs[f'{g_name}: {ret_str}'] = success
        return render_template('examples.html',example_design_form=example_design_form,ret_vals=ret_strs) 
    return render_template('examples.html',example_design_form=example_design_form)

@server.route('/download_example', methods=['GET', 'POST'])
def download_example():
    return send_from_directory(static_dir, "nor_gate.xml", as_attachment=True)

@server.before_request
def before_request_func():
    if current_user.get_id() is None:
        return
    user_dir = os.path.join(sessions_dir, current_user.get_id())
    try:
        os.makedirs(user_dir)
    except FileExistsError:
        pass
    session["user_dir"] = user_dir
    _handle_restore_dir()


def _convert_file(fn,name,ct):
    try:
        file_convert(graph.driver, fn, name, convert_type=ct)
    except (SAXParseException,ParserError):
        return False,"Incorrect file type."
    except Exception as ex:
        return False,ex
    return True, "Graph added successfully."


def _add_graph_forms():
    gns = graph.get_design_names()
    user_d_names = _get_user_gn(gns)
    remove_graph = forms.add_remove_graph_form(user_d_names)
    export_graph = forms.add_export_graph_form(user_d_names)
    return remove_graph,export_graph


def _is_admin():
    admin = login_manager.admin
    if admin.username == current_user.get_id() and admin.password == current_user.password:
        return True
    return False


def _get_user_gn(names):
    user_gn_file = os.path.join(sessions_dir,current_user.get_id(),user_gns)
    if not os.path.isfile(user_gn_file):
        return []
    with open(user_gn_file) as f:
        data = json.load(f)
        return list(set(data) & set(names))


def _add_user_gn(gn):
    user_gn_file = os.path.join(sessions_dir,current_user.get_id(),user_gns)
    data = [gn]
    if os.path.isfile(user_gn_file):
        with open(user_gn_file) as f:
            data += json.load(f)
    with open(user_gn_file, 'w') as outfile:
        json.dump(data, outfile)


def _remove_user_gn(gn):
    user_gn_file = os.path.join(sessions_dir,current_user.get_id(),user_gns)
    if not os.path.isfile(user_gn_file):
        return
    with open(user_gn_file) as f:
        data = json.load(f)
    data.remove(gn)
    with open(user_gn_file, 'w') as outfile:
        json.dump(data, outfile)


def _save_truth_graph():
    if not os.path.isdir(truth_save_dir):
        os.mkdir(truth_save_dir)
    out_fn = os.path.join(
        truth_save_dir, time.strftime("%Y%m%d-%H%M%S")+".json")
    graph.truth.save(out_fn)


def _handle_restore_dir():
    cur_time = time.time()
    times = []
    if not os.path.isdir(truth_save_dir):
        os.mkdir(truth_save_dir)
    if len(os.listdir(truth_save_dir)) == 0:
        _save_truth_graph()
        return

    for fn in os.listdir(truth_save_dir):
        fn = os.path.join(truth_save_dir, fn)
        times.append(cur_time - os.path.getmtime(fn))
    min_t = min(times, key=lambda x: float(x))
    if min_t > 86400:
        _save_truth_graph()

    files = os.listdir(truth_save_dir)
    while len(files) > 5:
        times = []
        for fn in files:
            fn = os.path.join(truth_save_dir, fn)
            times.append((cur_time - os.path.getmtime(fn), fn))
        max_t = max(times, key=lambda x: x[0])
        os.remove(max_t[1])
        files = os.listdir(truth_save_dir)


def _upload_graph(upload):
    ft = upload.file_type.data
    fn, gn = form_handlers.handle_upload(upload, session["user_dir"])
    if hasattr(upload,"run_mode"):
        rm = upload.run_mode.data
    else:
        rm = None
    graph.remove_design(gn)
    _add_user_gn(gn)
    success,ret_str = _convert_file(fn, gn, ft)
    err_string = None
    if not success:
        err_string = ret_str
    return gn,rm,err_string


def _get_evaluator_descriptions(feedback):
    descriptions = {}
    evaluators = {k.__class__.__name__: k for k in evaluator.get_evaluators()}

    def ged(d):
        for k, v in d.items():
            desc = evaluators[k].__doc__
            if desc is None:
                desc = ""
            descriptions[k] = desc
            if "evaluators" in v:
                ged(v["evaluators"])
    ged(feedback["evaluators"])
    return descriptions

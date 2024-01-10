import os
import json
import re
from flask_wtf import FlaskForm
from wtforms import SubmitField
from wtforms import TextAreaField
from wtforms import SelectField
from wtforms import BooleanField
from wtforms import FileField
from wtforms import validators
from wtforms import FormField
from wtforms.form import BaseForm
from wtforms import PasswordField
from wtforms import FieldList
graph_choices = [('SBOL', 'SBOL'), ("GBK", "Genbank")]
r_mode = [("automated", "Automated"), ("semi", "Semi-Automated")]

class SubmitForm(FlaskForm):
    class Meta:
        csrf = False
    submit = SubmitField('Submit')


class UploadForm(FlaskForm):
    class Meta:
        csrf = False
    submit_upload = SubmitField('Submit')
    upload = FileField('Upload File', validators=[validators.InputRequired()])


def add_truth_graph_form(directory,**kwargs):
    class ModifyTruthGraphForm(FlaskForm):
        class Meta:
            csrf = False
        tg_save = SubmitField('Save')
        tg_reseed = SubmitField('Reset (All Information will be lost.)')
        tg_expand = SubmitField('Expand')
        tg_restore = SubmitField('Restore')
    files = []
    for c in os.listdir(directory):
        desc = c.split(".")[0]
        date,time = desc.split("-")
        desc = f'{date[6:]}/{date[4:6]}/{date[:4]} - {time[:2]} : {time[2:4]}'
        files.append((c,desc))
    setattr(ModifyTruthGraphForm, "files", SelectField("Files", choices=files))
    return ModifyTruthGraphForm(**kwargs)

class PasteForm(FlaskForm):
    class Meta:
        csrf = False
    submit_paste = SubmitField('Submit')
    paste = TextAreaField('Paste', validators=[validators.InputRequired()])

class CreateUserForm(FlaskForm):
    class Meta:
        csrf = False
    username = TextAreaField("Username", validators=[validators.InputRequired()])
    password = PasswordField("Password", validators=[validators.InputRequired()])
    submit = SubmitField('Submit')

class CreateAdminForm(FlaskForm):
    class Meta:
        csrf = False
    username = TextAreaField("Username", validators=[validators.InputRequired()])
    password = PasswordField("Password", validators=[validators.InputRequired()])
    submit = SubmitField('Submit')

class AdminLogoutForm(FlaskForm):
    class Meta:
        csrf = False
    submit = SubmitField('Logout')

class UploadDesignForm(UploadForm):
    class Meta:
        csrf = False
    file_type = SelectField("Datatype", choices=graph_choices)

class UploadEnhanceDesignForm(UploadDesignForm):
    class Meta:
        csrf = False
    run_mode = BooleanField("Run Mode")

class UploadGraphForm(UploadDesignForm):
    class Meta:
        csrf = False
    graph_name = TextAreaField('Graph Name (Optional)')

class PasteGraphForm(PasteForm):
    class Meta:
        csrf = False
    file_type = SelectField("Datatype", choices=graph_choices)
    graph_name = TextAreaField('Graph Name (Optional)')

class SynbioGraphForm(FlaskForm):
    class Meta:
        csrf = False
    submit_sbh = SubmitField('Submit')
    pmid = TextAreaField('ID', validators=[validators.InputRequired()])
    graph_name = TextAreaField('Graph Name (Optional)')

class ConnectorFormTrue(FlaskForm):
    class Meta:
        csrf = False
    cft_submit = SubmitField('Yes')


class ConnectorFormFalse(FlaskForm):
    class Meta:
        csrf = False
    cff_submit = SubmitField('No')

class LargeGraphForm(FlaskForm):
    class Meta:
        csrf = False
    lg_confirm = SubmitField('Continue')
    lg_decline = SubmitField("Return")

def add_remove_graph_form(choices, **kwargs):
    class RemoveGraphForm(FlaskForm):
        class Meta:
            csrf = False
        submit = SubmitField('Remove')
    setattr(RemoveGraphForm, "graphs", SelectField(
        "Graph Name", choices=[(c, c) for c in choices]))
    return RemoveGraphForm(**kwargs)

def add_evaluate_graph_form(choices, **kwargs):
    class EvalGraphForm(FlaskForm):
        class Meta:
            csrf = False
        submit = SubmitField('Submit')
    setattr(EvalGraphForm, "graphs", SelectField(
        "Graph Name", choices=[(c, c) for c in choices]))
    return EvalGraphForm(**kwargs)

def add_choose_graph_form(choices, **kwargs):
    class ChooseGraphForm(FlaskForm):
        class Meta:
            csrf = False
        submit = SubmitField('Submit')
        run_mode = BooleanField("Automated")
    setattr(ChooseGraphForm, "graphs", SelectField(
        "Graph Name", choices=[(c, c) for c in choices]))
    return ChooseGraphForm(**kwargs)


def add_export_graph_form(choices, **kwargs):
    class ExportGraphForm(FlaskForm):
        class Meta:
            csrf = False
        export = SubmitField('Export')
    setattr(ExportGraphForm, "e_graphs", SelectField(
        "Graph Name", choices=[(c, c) for c in choices]))
    return ExportGraphForm(**kwargs)


def add_remove_projection_form(choices, **kwargs):
    class RemoveProjectionForm(FlaskForm):
        class Meta:
            csrf = False
        submit = SubmitField('Remove')
    choices = ["Remove All"] + choices
    setattr(RemoveProjectionForm, "graphs", SelectField(
        "Projection Name", choices=[(c, c) for c in choices]))
    return RemoveProjectionForm(**kwargs)


def add_graph_name_form(choices, **kwargs):
    class ExportGraphForm(FlaskForm):
        class Meta:
            csrf = False
        submit = SubmitField('Submit')
    setattr(ExportGraphForm, "graphs", SelectField(
        "Graph Name", choices=[(c, c) for c in choices]))
    return ExportGraphForm(**kwargs)


def add_semi_canonicaliser_form(choices, **kwargs):
    class SemiCanonicaliserGraphForm(FlaskForm):
        class Meta:
            csrf = False
        submit_semi_canonicaliser = SubmitField('Submit')
        close = SubmitField("Cancel")
    fields = []
    for k,v in choices.items():
        data = {"label":k}
        identifier = k
        choices = [("none","none")]
        for s in v:
            s_str = f'{str(s[0])} - {s[1]}'
            key = [s[0].get_key(),s[0].get_type(),s[0].properties]
            choices.append((key,s_str))
        data["choices"] = choices
        fields.append((identifier,SelectField,data))
    stage_form = form_from_fields([(field_id,f_type(**data)) for 
                                   field_id,f_type,data in fields])
    setattr(SemiCanonicaliserGraphForm, "forms", FormField(stage_form))
    return SemiCanonicaliserGraphForm(**kwargs)



def add_enhancement_form(choices, **kwargs):
    class ChooseGraphForm(FlaskForm):
        class Meta:
            csrf = False
        submit = SubmitField('Submit')
        automate = BooleanField("Automated")
    setattr(ChooseGraphForm, "graphs", SelectField(
        "Graph Name", choices=[(c, c) for c in choices]))
    return ChooseGraphForm(**kwargs)

def add_semi_enhancer_form(choices, **kwargs):
    stage_forms = []
    class EnhancerMainForm(FlaskForm):
        submit_enhancer = SubmitField("Submit")
        cancel_enhancer = SubmitField("Cancel")
    for enhancer,enhancements in choices.items():
        class EnhancerForm(FlaskForm):
            class Meta:
                csrf = False
            name = enhancer
        setattr(EnhancerForm, "num_enhancements", len(enhancements))
        enable_all_id = f'{enhancer} enable_all'
        setattr(EnhancerForm, enable_all_id,BooleanField(id="enable_all"))
        
        enhancement_forms = []
        for subject,choices in enhancements.items():
            choice_fields = []
            class ChoiceForm(FlaskForm):
                class Meta:
                    csrf = False
                name = subject
            for choice,details in choices.items():
                field_id = f'{enhancer} {subject} {choice}'
                data = {"label":details["comment"],"description": details["score"]}
                choice_fields.append((field_id,BooleanField,data))

            choice_form = form_from_fields([(field_id,f_type(**data)) for 
                                            field_id,f_type,data in choice_fields])
            setattr(ChoiceForm, "choices",FormField(choice_form))
            enhancement_forms.append(ChoiceForm())

        setattr(EnhancerForm, "enhancements",enhancement_forms)
        stage_forms.append(EnhancerForm())
    setattr(EnhancerMainForm, "forms", stage_forms)
    return EnhancerMainForm(**kwargs)

def create_example_design_form(expanation_file, **kwargs):
    class ExampleDesignForm(FlaskForm):
        class Meta:
            csrf = False
        submit_example = SubmitField('Submit')
        close = SubmitField("Cancel")
    with open(expanation_file) as f:
        data = json.load(f)
    examples = []
    for k,v in data.items():
        data = {"label":k.split(".")[0],"description":v}
        identifier = k
        examples.append((identifier,BooleanField,data))
    stage_form = form_from_fields([(field_id,f_type(**data)) for field_id,f_type,data in examples])
    setattr(ExampleDesignForm, "examples",FormField(stage_form))
    return ExampleDesignForm(**kwargs)

def add_remove_design_admin_form(user_designs,**kwargs):
    class DesignsForm(FlaskForm):
        class Meta:
            csrf = False
        submit_rda = SubmitField('Submit')
    d_forms = []
    for user,d_names in user_designs.items():
        for d_name in d_names:
            data = {"label":d_name,"description": user}
            identifier = d_name
            d_forms.append((identifier,BooleanField,data))
    stage_form = form_from_fields([(field_id,f_type(**data)) 
                                   for field_id,f_type,data in d_forms])
    setattr(DesignsForm, "d_forms",FormField(stage_form))
    return DesignsForm(**kwargs)

def add_remove_user_admin_form(d_names,**kwargs):
    class UsersForm(FlaskForm):
        class Meta:
            csrf = False
        submit_rua = SubmitField('Submit')
    u_forms = []
    for d_name in d_names:
        print(d_name)
        data = {"label":d_name}
        identifier = d_name
        u_forms.append((identifier,BooleanField,data))
    stage_form = form_from_fields([(field_id,f_type(**data)) 
                                   for field_id,f_type,data in u_forms])
    setattr(UsersForm, "u_forms",FormField(stage_form))
    return UsersForm(**kwargs)

def build_truth_query_form(handlers, **kwargs):
    class TruthQueryForm(FlaskForm):
        class Meta:
            csrf = False
        submit_query = SubmitField('Submit')
        query = TextAreaField('Query')
        choices = []
        examples = {}
        descriptions = {}
        for handler in handlers:
            name = handler.get_name()
            description = handler.get_description()
            example = handler.get_example()
            choices.append((name,name))
            examples[name] = example
            descriptions[name] = description
        query_type = SelectField("Query Type", choices=choices)
        descriptions = descriptions
        examples = examples

    return TruthQueryForm(**kwargs)

class TruthResultFieldForm(FlaskForm):
    class Meta:
        csrf = False
    load = SubmitField()
    positive = SubmitField()
    negative = SubmitField()

def build_tgrf(results,query_type):
    forms = []
    for index,(source,results) in enumerate(results.items()):
        for result in results:
            class TruthResultFieldForm(FlaskForm):
                class Meta:
                    csrf = False    
                load = SubmitField(index)
                positive = SubmitField()
                negative = SubmitField()
            conf,entity = result
            description = entity["description"]
            entity = entity["entity"]
            if is_url(entity):
                setattr(TruthResultFieldForm, "uri", entity)
            else:
                setattr(TruthResultFieldForm, "name", entity)
            setattr(TruthResultFieldForm,"identifier",f'{source} - {entity} - {query_type}')
            setattr(TruthResultFieldForm, "confidence", conf)
            setattr(TruthResultFieldForm, "description", description)
            forms.append(TruthResultFieldForm())
    return forms

def form_from_fields(fields):
    def create_form(**kwargs):
        form = BaseForm(fields)
        form.process(**kwargs)
        return form
    return create_form


def is_url(string):
    # Regular expression pattern for URL matching
    url_pattern = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(url_pattern, string) is not None
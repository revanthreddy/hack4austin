import cherrypy
import json
from simple_salesforce import Salesforce

USERNAME = 'viki89@gmail.com.hack4austi'
PASSWORD = 'june1989'
SECURITY_TOKEN = '3Z2NaZbQHuJgz3MwGtgNEDfr'

class Root(object):

   def __init__(self):
      self.login()

   def login(self):
      self._sf = Salesforce(username=USERNAME, password=PASSWORD, security_token=SECURITY_TOKEN, sandbox=True)

   @cherrypy.expose
   def index(self):
      return "hello"

   @cherrypy.expose
   def get_all_teachers(self, **kwargs):
      soql = "select id,name,email from Contact where contact_type__c='teacher'"
      try:
         results = self._sf.query_all(soql)
         return json.dumps({'ok': True, 'results': results})
      except Exception as ex:
         return json.dumps({'ok': False, 'error': ex.message})

   @cherrypy.expose
   def get_all_students(self, **kwargs):
      soql = 'select id,name,placement_address__c from Student__c'
      try:
         results = self._sf.query_all(soql)
         return json.dumps({'ok': True, 'results': results})
      except Exception as ex:
         return json.dumps({'ok': False, 'error': ex.message})

   @cherrypy.expose
   def submit_lesson(self, params=None, **kwargs):
      params = json.loads(params)
      return json.dumps({'ok': True})

   @cherrypy.expose
   def get_teacher(self, teacher_id=None, **kwargs):
      if not teacher_id:
         return json.dumps({'ok': False, 'error': 'teacher_id not given'})
      try:
         teacher = self._sf.Contact.get(teacher_id)
         results = {}
         for k in ['attributes', 'Name', 'Email']:
            results[k] = teacher[k]
         return json.dumps({'ok': True, 'results': results})
      except Exception as ex:
         return json.dumps({'ok': False, 'error': ex.message})

   @cherrypy.expose
   def get_student(self, student_id=None, **kwargs):
      if not student_id:
         return json.dumps({'ok': False, 'error': 'student_id not given'})
      try:
         student = self._sf.Student__c.get(student_id)
         results = {}
         for k in ['attributes', 'Name', 'Placement_Address__c']:
            results[k] = student[k]
         return json.dumps({'ok': True, 'results': results})
      except Exception as ex:
         return json.dumps({'ok': False, 'error': ex.message})

if __name__ == '__main__':
   conf = {
      'global': {
         'server.socket_host': '0.0.0.0',
         'server.socket_port': 17071,
         'server.thread_pool': 300,
         'server.max_request_body_size': 300 * 1024 * 1024,
      }
   }

   cherrypy.quickstart(Root(), '/', conf)

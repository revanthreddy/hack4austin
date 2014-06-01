import cherrypy
import json
from simple_salesforce import Salesforce
import pymongo
from datetime import datetime
from bson.objectid import ObjectId

USERNAME = 'viki89@gmail.com.hack4austi'
PASSWORD = 'june1989'
SECURITY_TOKEN = '3Z2NaZbQHuJgz3MwGtgNEDfr'

MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017

mongo_db = pymongo.MongoClient(MONGODB_HOST, MONGODB_PORT).test

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
      soql = "select id,name,e_mail__c from Teacher__c"
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
   def get_teacher(self, teacher_id=None, **kwargs):
      if not teacher_id:
         return json.dumps({'ok': False, 'error': 'teacher_id not given'})
      try:
         teacher = self._sf.Teacher__c.get(teacher_id)
         results = {}
         for k in ['attributes', 'Name', 'E_mail__c']:
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

   @cherrypy.expose
   def save_lesson_log(self, submit=None, **kwargs):
      body = cherrypy.request.body.read()
      if not body:
         return json.dumps({'ok': False, 'error': 'no message body'})
      params = json.loads(body)
      if 'teacherName' not in params:
         return json.dumps({'ok': False, 'error': 'teacherName not given'})
      if 'studentName' not in params:
         return json.dumps({'ok': False, 'error': 'studentName not given'})

      if not submit:
         result = self.save_to_mongo(params)
         return json.dumps(result)

      # get teacher id
      soql = "select id from teacher__c where name='%s'" % (params['teacherName'])
      try:
         teacher = self._sf.query(soql)
      except Exception as ex:
         return json.dumps({'ok': False, 'error': ex.message})

      if len(teacher['records']) <= 0:
         return json.dumps({'ok': False, 'error': 'teacherName not found'})
      teacher_id = teacher['records'][0]['Id']

      # get student id
      soql = "select id from student__c where name='%s'" % (params['studentName'])
      try:
         student = self._sf.query(soql)
      except Exception as ex:
         return json.dumps({'ok': False, 'error': ex.message})

      if len(student['records']) <= 0:
         return json.dumps({'ok': False, 'error': 'studentName not found'})
      student_id = student['records'][0]['Id']

      # get lesson id
      soql = "select id from lesson__c where teacher__c='%s' and student__c='%s'" % (teacher_id, student_id)
      try:
         lesson = self._sf.query(soql)
      except Exception as ex:
         return json.dumps({'ok': False, 'error': ex.message})

      data = {'name': str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
              'Teacher_s_Name__c': teacher_id,
              'student__c': student_id,
              'life_skills__c': int(float(params.get('studentProgressMultipleSkills', '0'))),
              'music_education__c': int(float(params.get('studentMusicProgressRank', '0'))),
              'length_of_lesson__c': 0,
              'lesson_notes__c': json.dumps(params, indent=0)
             }

      if len(lesson['records']) > 0:
         data['lesson__c'] = lesson['records'][0]['Id']

      result = self._sf.Lesson_Logs__c.create(data)
      return json.dumps({'ok': True})

   @cherrypy.expose
   def get_lesson_logs(self, **kwargs):
      lessons = mongo_db.lessons.find()
      lessons_array = []
      for lesson in lessons:
         lessons_array.append({'id': str(lesson['_id']), 'params': lesson['params']})
      return json.dumps({'ok': True, 'results': lessons_array})

   @cherrypy.expose
   def get_lesson_log(self):
      body = cherrypy.request.body.read()
      if 'lesson_id' not in body:
         return json.dumps({'ok': False, 'error': 'lesson_id not given'})
      lesson_id = json.loads(body)['lesson_id']
      try:
         lesson = mongo_db.lessons.find_one({'_id': ObjectId(lesson_id)})
         return json.dumps({'ok': True, 'results': lesson['params']})
      except Exception as ex:
         return json.dumps({'ok': False, 'error': ex.message})

   def save_to_mongo(self, params):
      if params.get('lesson_id'):
         # update existing record
         id = params.get('lesson_id')
         mongo_db.lessons.update({'_id': ObjectId(id)}, {"$set": {'params': params}})
         return {'ok': True}
      else:
         # create new record
         id = mongo_db.lessons.insert({'params': params})
         return {'ok': True, 'id': str(id)}

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

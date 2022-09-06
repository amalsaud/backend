import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# Global function for pagination
def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]

  return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  CORS(app, resources={r"/api/*": {"origins": "*"}})

  # CORS Headers
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,True')
    response.headers.add('Access-Control-Allow-Headers', 'GET,POST,PATCH,DELETE,OPTIONS')
    return response

  #---------------------------------------------------#
  # Endpoints
  #---------------------------------------------------#

  # Endpoint to handle GET requests for all available categories
  @app.route('/categories')
  def retrieve_categories():
    all_categories = Category.query.order_by(Category.id).all()
    categories = {}
    for category in all_categories:
      categories[category.id] = category.type

    return jsonify({
      'success': True,
      'categories': categories
    })
    
  # Endpoint to handle GET requests for questions, including pagination
  @app.route('/questions')
  def retrieve_questions():
    selection = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request, selection)

    all_categories = Category.query.order_by(Category.id).all()
    categories = {}
    for category in all_categories:
      categories[category.id] = category.type

    if len(current_questions) == 0:
      abort(404)

    return jsonify({
        'success': True,
        'questions': current_questions,
        'categories': categories,
        'total_questions': len(Question.query.all())
    })

  # Endpoint to DELETE question using a question ID
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()

      if question is None:
        abort(404)
      
      question.delete()
      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)

      return jsonify({
        'success': True,
        'deleted': question_id,
        'questions': current_questions,
        'total_questions': len(Question.query.all())
      })

    except:
      abort(422)
  
  # Endpoint to POST a new question
  @app.route('/questions', methods=['POST'])
  def create_question():
    body = request.get_json()

    new_question = body.get('question', None)
    new_answer = body.get('answer', None)
    new_category = body.get('category', None)
    new_difficulty = body.get('difficulty', None)

    try:
      question = Question(question=new_question, answer=new_answer, category=new_category, difficulty=new_difficulty)
      question.insert()

      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)

      return jsonify({
        'success': True,
        'created': question.id,
        'questions': current_questions,
        'total_questions': len(Question.query.all())
      })

    except:
      abort(422)
  
  # a POST endpoint to get questions based on a search term
  @app.route('/questions/search', methods=['POST'])
  def search_questions():
    body = request.get_json()
    search = body.get('searchTerm', None)

    selection = Question.query.filter(Question.question.ilike('%' + search + '%')).all()
    current_questions = paginate_questions(request, selection)

    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(Question.query.all())
    })

  # GET endpoint to get questions based on category
  @app.route('/categories/<int:category_id>/questions')
  def get_category_questions(category_id):
    category = Category.query.filter(Category.id == category_id).one_or_none()

    if category is None:
      abort(404)
    
    selection = Question.query.order_by(Question.id).filter(Question.category == category_id).all() 
    current_questions = paginate_questions(request, selection)

    return jsonify({
      'success': True,
      'questions': current_questions
    })

  # POST endpoint to get questions to play the quiz
  @app.route('/quizzes', methods=['POST'])
  def play_quiz():
    body = request.get_json()
    quiz_category = body.get('quiz_category', None)
    previous_questions = body.get('previous_questions', None)
    
    try:
      if quiz_category['id'] == 0:
        selection = Question.query.filter(Question.id.notin_(previous_questions)).all()
      else:
        selection = Question.query.filter(Question.category == quiz_category['id']).filter(Question.id.notin_(previous_questions)).all()

      if len(selection) > 0:
        question = random.choice(selection).format()
      else:
        question = None

      return jsonify({
        'success': True,
        'question': question
      })
    except:
      abort(422)

  #---------------------------------------------------#
  # Error handlers for expected errors
  #---------------------------------------------------#
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success": False,
      "error": 404,
      "message": "resource not found"
    }), 404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      "success": False,
      "error": 422,
      "message": "unprocessable"
    }), 422

  return app

    
from http.server import BaseHTTPRequestHandler
import json
import os

# Questions data embedded directly
QUESTIONS_DATA = {
    "sections": [
        {
            "id": "1",
            "title": "Problem Definition",
            "subsections": [
                {
                    "id": "1.1",
                    "title": "Problem Statement",
                    "questions": [
                        {"id": "1.1.1", "question": "What is the core problem you are trying to solve?", "type": "text"},
                        {"id": "1.1.2", "question": "Who experiences this problem?", "type": "text"},
                        {"id": "1.1.3", "question": "How do users currently solve this problem?", "type": "text"},
                        {"id": "1.1.4", "question": "What is the impact of not solving this problem?", "type": "text"},
                        {"id": "1.1.5", "question": "How frequently do users encounter this problem?", "type": "text"}
                    ]
                }
            ]
        },
        {
            "id": "2",
            "title": "User Research",
            "subsections": [
                {
                    "id": "2.1",
                    "title": "Target Users",
                    "questions": [
                        {"id": "2.1.1", "question": "Who is your primary target user?", "type": "text"},
                        {"id": "2.1.2", "question": "What are their key characteristics or demographics?", "type": "text"},
                        {"id": "2.1.3", "question": "What are their goals and motivations?", "type": "text"},
                        {"id": "2.1.4", "question": "What are their pain points?", "type": "text"},
                        {"id": "2.1.5", "question": "What is their technical proficiency level?", "type": "text"}
                    ]
                }
            ]
        },
        {
            "id": "3",
            "title": "Solution Overview",
            "subsections": [
                {
                    "id": "3.1",
                    "title": "Proposed Solution",
                    "questions": [
                        {"id": "3.1.1", "question": "What is your proposed solution?", "type": "text"},
                        {"id": "3.1.2", "question": "How does it solve the problem?", "type": "text"},
                        {"id": "3.1.3", "question": "What are the key features?", "type": "text"},
                        {"id": "3.1.4", "question": "What makes this solution unique?", "type": "text"},
                        {"id": "3.1.5", "question": "What are the technical requirements?", "type": "text"}
                    ]
                }
            ]
        }
    ]
}

def cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Content-Type': 'application/json'
    }

class handler(BaseHTTPRequestHandler):
    def send_cors_headers(self):
        for key, value in cors_headers().items():
            self.send_header(key, value)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
        return

    def do_GET(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(QUESTIONS_DATA).encode())
        return

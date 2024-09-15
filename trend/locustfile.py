import os
import random
import string
from locust import HttpUser, TaskSet, task, between


class UserBehavior(TaskSet):
    def generate_random_string(self, length=8):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    @task(1)
    def register_user(self):
        file_path = os.path.abspath('/Users/raniaalbliwi/TREND/images/avatar.jpeg')
        username = self.generate_random_string()
        email = f"{username}@example.com"
        password = 'password123'
        response = self.client.post("/register/", 
            files={
                'avatar': ('avatar.jpg', open(file_path, 'rb'), 'image/jpeg')
            },
            data={
                'username': username,
                'email': email,
                'password': password,
                'password2': password,
            }
        )
        print(response.text)

class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(1, 5)  # Simulate a user waiting between 1 to 5 seconds between tasks


class VlogTasks(TaskSet):
    def generate_random_string(self, length=8):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    @task
    def create_vlog(self):

        file_path = os.path.abspath('/Users/raniaalbliwi/TREND/images/test_video.mp4')
        # Replace these with the actual data for your test
        data = {
            "title": self.generate_random_string(),
            "description": self.generate_random_string(),
           
        }
        files = {
            "vlog": ("test_video.mp4", open(file_path, 'rb'), "video/mp4")
        }       
        
        response = self.client.post("/vlogs/create/",data=data, files=files)
        if response.status_code == 201:
            print("Vlog created successfully")
        else:
            print("Failed to create vlog", response.status_code, response.text)


class VlogUser(HttpUser):
    auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzIzNDAyNTQ0LCJpYXQiOjE3MjMzOTg5NDQsImp0aSI6IjZkMzVjOGM2YmI0YTQwNDk5ZDAxYWJiYzA5YWQ2ZDcwIiwidXNlcl9pZCI6Mn0.dI7e8ctLhOOXwsUxW6MGPV-I3GsK5K-9K4RWCVuU-gg"
    
    def on_start(self):
        # Add authentication headers to each request
        self.client.headers.update({
            "Authorization": f"Bearer {self.auth_token}"
        })

    tasks = [VlogTasks]
    wait_time = between(1, 5)  # Wait between 1 and 5 seconds between tasks


class WebsiteUser(HttpUser):
    wait_time = between(1, 5)  # Wait time between tasks
    auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzIzNDAyNTQ0LCJpYXQiOjE3MjMzOTg5NDQsImp0aSI6IjZkMzVjOGM2YmI0YTQwNDk5ZDAxYWJiYzA5YWQ2ZDcwIiwidXNlcl9pZCI6Mn0.dI7e8ctLhOOXwsUxW6MGPV-I3GsK5K-9K4RWCVuU-gg"
    
    def on_start(self):
        # Add authentication headers to each request
        self.client.headers.update({
            "Authorization": f"Bearer {self.auth_token}"
        })
    @task
    def get_posts(self):
        response = self.client.get("/posts/")
        if response.status_code == 200:
            print("Successfully fetched posts")
        else:
            print("Failed to fetch posts", response.status_code, response.text)
    
    @task
    def get_vlogs(self):
        response = self.client.get("/vlogs/")
        if response.status_code == 200:
            print("Successfully fetched vlogs")
        else:
            print("Failed to fetch vlogs", response.status_code, response.text)
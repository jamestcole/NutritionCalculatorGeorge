#So I would like to creat a fastapi web app that has the following funcitonality: it connects to a database called menu_items.db in a different directory with the table name meals_and_ingredients. It has 4 pages, one is the home page where it gives 7 dropdown menus which the user can select the meal entry from the database, it has 3 buttons underneath this: "Add a meal", "Edit a meal" and "Generate ingredients", each linking to a different page. The add a meal page will have the functionality with two entry boxes where the user can input the meal name and the ingredients in that meal, underneath will be a save button which will save the name to the meal column and the corresponding ingredients to the ingredients column in the database, it will also redirect the user back to the homepage. The edit a meal page will bring up a selection menu where the user can select the meal values from the database, then once they have a selected value, two new entry boxes will appear, filled with the values from that selected meal, they will then be able to edit these values and underneath it all will be a save meal button, which will update the database with the new values. The final page will be the generate ingredients page, which will take all the values from the dropdown menus on the home page and return all of the ingredients in an ordered list, which if there are duplicate values, will display as "Value xn", where n is the number of times the value is duplicated.
import uvicorn
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import sqlite3

from pathlib import Path

app = FastAPI()
templates = Jinja2Templates(directory="templates")
favicon_path = Path(__file__).resolve().parent / "test" / "favicon.ico"

def get_db_connection():
    db_path = Path(__file__).resolve().parent.parent / "menu_items.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    conn = get_db_connection()
    meals = conn.execute('SELECT meal FROM meals_and_ingredients ORDER BY meal').fetchall()
    conn.close()
    return templates.TemplateResponse("home.html", {"request": request, "meals": meals, "days_of_week": days_of_week})

@app.get("/add_meal", response_class=HTMLResponse)
async def add_meal(request: Request):
    return templates.TemplateResponse("add_meal.html", {"request": request})

@app.post("/add_meal")
async def add_meal(request: Request):
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    form_data = await request.form()
    meal = form_data['meal']
    ingredients = form_data['ingredients']
    conn = get_db_connection()
    conn.execute('INSERT INTO meals_and_ingredients (meal, ingredients) VALUES (?, ?)', (meal, ingredients))
    conn.commit()
    conn.close()
    return templates.TemplateResponse("add_meal.html", {"request": request, "message": "Meal added successfully!"})

@app.get("/edit_meal", response_class=HTMLResponse)
async def edit_meal(request: Request):
    conn = get_db_connection()
    meals = conn.execute('SELECT meal, ingredients FROM meals_and_ingredients ORDER BY meal').fetchall()
    meals = [dict(meal) for meal in meals]
    conn.close()
    return templates.TemplateResponse("edit_meal.html", {"request": request, "meals": meals})

@app.post("/edit_meal")
async def edit_meal(request: Request):
    conn = get_db_connection()
    meals = conn.execute('SELECT meal, ingredients FROM meals_and_ingredients ORDER BY meal').fetchall()
    meals = [dict(meal) for meal in meals]
    conn.close()

    form_data = await request.form()
    if 'delete_meal' in form_data:
        meal_to_delete = form_data['meal_to_delete']
        conn = get_db_connection()
        conn.execute('DELETE FROM meals_and_ingredients WHERE meal=?', (meal_to_delete,))
        conn.commit()
        conn.close()
        return templates.TemplateResponse("edit_meal.html", {"request": request, "meals": meals, "message": "Meal deleted successfully!"})
    else:
        meal_to_edit = form_data['meal_to_edit']
        new_meal_name = form_data['new_meal_name']
        new_ingredients = form_data['new_ingredients']
        conn = get_db_connection()
        conn.execute('UPDATE meals_and_ingredients SET meal=?, ingredients=? WHERE meal=?', (new_meal_name, new_ingredients, meal_to_edit))
        conn.commit()
        conn.close()
        return templates.TemplateResponse("edit_meal.html", {"request": request, "meals": meals, "message": "Meal edited successfully!"})

@app.get("/generate_ingredients", response_class=HTMLResponse)
async def generate_ingredients(request: Request):
    meals = request.query_params.getlist("meal")
    ingredients_list = []
    for meal in meals:
        if meal:
            conn = get_db_connection()
            ingredients = conn.execute('SELECT ingredients FROM meals_and_ingredients WHERE meal=?', (meal,)).fetchone()[0]
            ingredients_list.extend([ingredient.strip() for ingredient in ingredients.split(",")])
            conn.close()

    ingredients_count = {}
    for ingredient in ingredients_list:
        if ingredient in ingredients_count:
            ingredients_count[ingredient] += 1
        else:
            ingredients_count[ingredient] = 1

    sorted_ingredients_count = dict(sorted(ingredients_count.items()))

    return templates.TemplateResponse("generate_ingredients.html", {"request": request, "ingredients_count": sorted_ingredients_count})

if __name__ == "__main__":
    uvicorn.run(app)

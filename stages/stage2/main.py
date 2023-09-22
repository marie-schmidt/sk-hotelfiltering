import json
import quart
import quart_cors
from quart import request

import semantic_kernel as sk
from semantic_kernel.planning.basic_planner import BasicPlanner
import config.add_completion_service
from plugins.HotelPlugin.Filter import Filter
from database import HOTELS

app = quart_cors.cors(quart.Quart(__name__), allow_origin="http://localhost:3000")

@app.get("/hotels")
async def get_hotels():
    return quart.Response(response=json.dumps(HOTELS), status=200)

@app.post("/hotels/filter")
async def filter_hotel():
    filter = await quart.request.get_json(force=True)

    # Copy the list of hotels in a new var
    filtered_hotels = HOTELS.copy()

    # We expect a name, address, stars and beds
    name = filter['name']
    if name != "":
        filtered_hotels = [hotel for hotel in filtered_hotels if name in hotel['name']]

    address = filter['address']
    if address != "":
        filtered_hotels = [hotel for hotel in filtered_hotels if address in hotel['address']]

    stars = filter['stars']
    if stars != "Stars":
        # Convert the stars to int
        stars = int(stars)
        filtered_hotels = [hotel for hotel in filtered_hotels if hotel['stars'] == stars]

    beds = filter['beds']
    if beds != "Beds":
        # Convert the beds to int
        beds = int(beds)
        filtered_hotels = [hotel for hotel in filtered_hotels if hotel['beds'] == beds]

    return quart.Response(response=json.dumps(filtered_hotels), status=200)

@app.post("/hotels/filter-with-semantickernel")
async def filter_hotel_with_sk():
    # Initialize the kernel
    kernel = sk.Kernel()
    # Add a text or chat completion service using either:
    # kernel.add_text_completion_service()
    # kernel.add_chat_service()
    kernel.add_completion_service()

    # Import the native functions
    kernel.import_skill(Filter(), "HotelPlugin")
    
    ask = "System: You summarize the users question into in a single sentence."
    ask = ask + "User: What hotels do we have in Belgium which have a maximum of 2 stars and has a nice a cinema?"

    planner = BasicPlanner()
    plan = await planner.create_plan_async(ask, kernel)
    print(plan)

    # Execute the plan
    result = await planner.execute_plan_async(plan, kernel)

    # Parse the json string to object
    print(result)
    return quart.Response(response=json.dumps(HOTELS), status=200)


@app.post("/hotels")
async def add_hotel():
    request = await quart.request.get_json(force=True)
    HOTELS.append(request)
    return quart.Response(response='OK', status=200)

@app.get("/logo.png")
async def plugin_logo():
    filename = 'logo.png'
    return await quart.send_file(filename, mimetype='image/png')

@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    host = request.headers['Host']
    with open("./.well-known/ai-plugin.json") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/json")

@app.get("/openapi.yaml")
async def openapi_spec():
    host = request.headers['Host']
    with open("openapi.yaml") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/yaml")

def main():
    app.run(debug=True, host="0.0.0.0", port=5003)

if __name__ == "__main__":
    main()
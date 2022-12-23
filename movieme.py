import discord
import pandas as pd
import logging
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger("m!")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


intents = discord.Intents.all()
intents.members = True

client = commands.Bot(command_prefix = "m!", intents = intents)

@client.event
async def on_ready():
        print('We have logged in as {0.user}'.format(client))

async def get_message(ctx):
    """Get movies from message"""
    logger.info("Retrieving movies...")
    message = ctx.channel.history(limit=1)
    message = message.lstrip('m! ').split(') ')
    return message

logger.info("Reading MovieLens data...")
# Load the MovieLens dataset
movies = pd.read_csv("movies.csv")
ratings = pd.read_csv("ratings.csv")

# Create a pivot table that calculates the average rating for each movie
movie_ratings = ratings.pivot_table(index="movieId", values="rating", aggfunc="mean")

# Function to recommend a new movie based on two movies specified by the user
async def recommend_movie(movie1, movie2):
    # Look up the two movies in the movies dataset
    movie1_details = movies[movies["title"] == movie1]
    movie2_details = movies[movies["title"] == movie2]
    
    # If either movie is not found in the dataset, return an error message
    if movie1_details.empty or movie2_details.empty:
        return "Sorry, one of the movies you entered was not found in the dataset."
    
    # Get the movie IDs for the two movies
    movie1_id = movie1_details["movieId"].iloc[0]
    movie2_id = movie2_details["movieId"].iloc[0]
    
    # Get the average ratings for the two movies
    movie1_rating = movie_ratings.loc[movie1_id]["rating"]
    movie2_rating = movie_ratings.loc[movie2_id]["rating"]
    
    # Find the movies that were rated by users who also rated both of the specified movies
    common_rated_movies = ratings[(ratings["movieId"] == movie1_id) | (ratings["movieId"] == movie2_id)]["userId"].unique()
    other_movies = ratings[ratings["userId"].isin(common_rated_movies)]
    
    # Calculate the average rating for each movie among the common users
    other_movie_ratings = other_movies.pivot_table(index="movieId", values="rating", aggfunc="mean")
    
    # Find the movie with the highest average rating among the common users, that is not one of the specified movies
    recommended_movie_id = other_movie_ratings[(other_movie_ratings.index != movie1_id) & (other_movie_ratings.index != movie2_id)].idxmax()[0]
    
    # Look up the recommended movie in the movies dataset
    recommended_movie = movies[movies["movieId"] == recommended_movie_id]
    
    # Return the title and average rating of the recommended movie
    return f"Based on the movies you specified, we recommend you watch: {recommended_movie['title'].iloc[0]} (average rating: {other_movie_ratings.loc[recommended_movie_id]['rating']:.1f})"

@client.command()
async def movieme(ctx):
    logger.info("Starting recommendations..")
    movies = await get_recent_message(ctx)
    recommendation = recommend_movie(movies[0], movies[1])
    await ctx.send(recommendation)

client.run(os.getenv("TOKEN")) 

import pandas as pd
import numpy as np
from sys import exc_info
import ast
import user_cluster


class userRequestedFor:
    def __init__(self, user_id, users_data, clusters_fixed, movies_df_fixed):
        self.users_data = users_data.copy()
        self.user_id = user_id
        # Find User Cluster
        user_clusters = clusters_fixed[clusters_fixed['userId'] == self.user_id]['Cluster']
        if (len(user_clusters) == 0):
            self.cluster_id = 0
        else:
            self.cluster_id = int(user_clusters.iloc[0])
        # Load User Cluster Movies Dataframe
        self.movies_list = movies_df_fixed
        self.cluster_movies = self.movies_list[self.cluster_id] # dataframe
        self.cluster_movies_list = list(self.cluster_movies['movieId']) # list
    def updatedFavouriteMoviesList(self, new_movie_Id):
        if new_movie_Id in self.cluster_movies_list:
            self.cluster_movies.loc[self.cluster_movies['movieId'] == new_movie_Id, 'Count'] += 1
        else:
            self.cluster_movies = self.cluster_movies.append([{'movieId':new_movie_Id, 'Count': 1}], ignore_index=True)
        self.cluster_movies.sort_values(by = ['Count'], ascending = False, inplace= True)
        self.movies_list[self.cluster_id] = self.cluster_movies

    def recommendMostFavouriteMovies(self):
        try:
            user_movies = user_cluster.getMoviesOfUser(self.user_id, self.users_data)
            cluster_movies_list = self.cluster_movies_list.copy()
            for user_movie in user_movies:
                if user_movie in cluster_movies_list:
                    cluster_movies_list.remove(user_movie)
            return [True, cluster_movies_list]
        except KeyError:
            err = "User history does not exist"
            print(err)
            return [False, err]
        except:
            err = 'Error: {0}, {1}'.format(exc_info()[0], exc_info()[1])
            print(err)
            return [False, err]
        

def get_movies_metadata(users_fav_movies):
    movies_metadata = pd.read_csv(
    './movies_metadata.csv', 
    usecols = ['id', 'genres', 'original_title'])

    movies_metadata = movies_metadata.loc[
        movies_metadata['id'].isin(list(map(str, np.unique(users_fav_movies['movieId']))))].reset_index(drop=True)
    return movies_metadata


def run_all(fav_movies_titles):
    users_fav_movies = user_cluster.get_user_fav_movies()
    movies_metadata = get_movies_metadata(users_fav_movies)
    fav_movies = list(movies_metadata[movies_metadata['original_title'].isin(fav_movies_titles)]['id'])
    fav_movies = [int(movie) for movie in fav_movies]
    fav_movies.sort()
    print(fav_movies)
    users = user_cluster.get_unique_users(users_fav_movies)
    new_user_id = max(users) + 1
    for movie in fav_movies:
        users_fav_movies.loc[len(users_fav_movies)] = [new_user_id, movie, 5]
    users_cluster = user_cluster.cluster_users(users_fav_movies)
    cluster_movies = user_cluster.cluster_movies(users_cluster, users_fav_movies)
    movies_df_fixed, clusters_fixed = user_cluster.fixClusters(cluster_movies, users_cluster, users_fav_movies, smallest_cluster_size = 6)
    recommendations = userRequestedFor(new_user_id, users_fav_movies, clusters_fixed, movies_df_fixed).recommendMostFavouriteMovies()[1]
    titles = []
    for movie in recommendations[:15]:
        title = list(movies_metadata.loc[movies_metadata['id'] == str(movie)]['original_title'])
        if title:
            titles.append(title[0])
    return titles
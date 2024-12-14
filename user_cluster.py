import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
from sklearn.cluster import KMeans


def get_user_fav_movies():
    ratings = pd.read_csv('./ratings_small.csv', usecols = ['userId', 'movieId','rating'])
    ratings = ratings[ratings['rating'] >= 4.0]
    users_fav_movies = ratings.loc[:, ['userId', 'movieId']]
    users_fav_movies = ratings.reset_index(drop = True)
    return users_fav_movies


def get_unique_users(users_fav_movies):
    return np.unique(users_fav_movies['userId'])

def get_users_movies_list(users_fav_movies):
    # users = a list of users IDs
    # users_data = a dataframe of users favourite movies or users watched movies
    users_movies_list = []
    users = get_unique_users(users_fav_movies)
    for user in users:
        users_movies_list.append(str(list(users_fav_movies[users_fav_movies['userId'] == user]['movieId'])).split('[')[1].split(']')[0])
    return users_movies_list


def get_sparse_matrix(list_of_str):
    # list_of_str = A list, which contain strings of users favourite movies separate by comma ",".
    # It will return us sparse matrix and feature names on which sparse matrix is defined 
    # i.e. name of movies in the same order as the column of sparse matrix
    cv = CountVectorizer(token_pattern = r'[^\,\ ]+', lowercase = False)
    sparseMatrix = cv.fit_transform(list_of_str)
    return sparseMatrix.A, cv.get_feature_names_out()



def cluster_users(users_fav_movies):
    users = get_unique_users(users_fav_movies)
    users_movies_list = get_users_movies_list(users_fav_movies)
    sparseMatrix, feature_names = get_sparse_matrix(users_movies_list)
    kmeans = KMeans(n_clusters=15, init = 'k-means++', max_iter = 300, n_init = 10, random_state = 0)
    clusters = kmeans.fit_predict(sparseMatrix)
    users_cluster = pd.DataFrame(np.concatenate((users.reshape(-1,1), clusters.reshape(-1,1)), axis = 1), columns = ['userId', 'Cluster'])
    return users_cluster
    

def cluster_movies(users_cluster, users_data):
    clusters = list(users_cluster['Cluster'])
    each_cluster_movies = list()
    for i in range(len(np.unique(clusters))):
        users_list = list(users_cluster[users_cluster['Cluster'] == i]['userId'])
        users_movies_list = list()
        for user in users_list:    
            users_movies_list.extend(list(users_data[users_data['userId'] == user]['movieId']))
        users_movies_counts = list()
        users_movies_counts.extend([[movie, users_movies_list.count(movie)] for movie in np.unique(users_movies_list)])
        each_cluster_movies.append(pd.DataFrame(users_movies_counts, columns=['movieId', 'Count']).sort_values(by = ['Count'], ascending = False).reset_index(drop=True))
    return each_cluster_movies


def getMoviesOfUser(user_id, users_fav_movies):
    return list(users_fav_movies[users_fav_movies['userId'] == user_id]['movieId'])


def fixClusters(clusters_movies_dataframes, users_cluster_dataframe, users_fav_movies, smallest_cluster_size = 11):
    # clusters_movies_dataframes: will be a list which will contain each dataframes of each cluster movies
    # users_cluster_dataframe: will be a dataframe which contain users IDs and their cluster no.
    # smallest_cluster_size: is a smallest cluster size which we want for a cluster to not remove
    each_cluster_movies = clusters_movies_dataframes.copy()
    users_cluster = users_cluster_dataframe.copy()
    # Let convert dataframe in each_cluster_movies to list with containing only movies IDs
    each_cluster_movies_list = [list(df['movieId']) for df in each_cluster_movies]
    # First we will prepair a list which containt lists of users in each cluster -> [[Cluster 0 Users], [Cluster 1 Users], ... ,[Cluster N Users]] 
    usersInClusters = list()
    total_clusters = len(each_cluster_movies)
    for i in range(total_clusters):
        usersInClusters.append(list(users_cluster[users_cluster['Cluster'] == i]['userId']))
    uncategorizedUsers = list()
    i = 0
    # Now we will remove small clusters and put their users into another list named "uncategorizedUsers"
    # Also when we will remove a cluster, then we have also bring back cluster numbers of users which comes after deleting cluster
    # E.g. if we have deleted cluster 4 then their will be users whose clusters will be 5,6,7,..,N. So, we'll bring back those users cluster number to 4,5,6,...,N-1.
    for j in range(total_clusters):
        if len(usersInClusters[i]) < smallest_cluster_size:
            uncategorizedUsers.extend(usersInClusters[i])
            usersInClusters.pop(i)
            each_cluster_movies.pop(i)
            each_cluster_movies_list.pop(i)
            users_cluster.loc[users_cluster['Cluster'] > i, 'Cluster'] -= 1
            i -= 1
        i += 1
    for user in uncategorizedUsers:
        elemProbability = list()
        user_movies = getMoviesOfUser(user, users_fav_movies)
        if len(user_movies) == 0:
            print(user)
        user_missed_movies = list()
        for movies_list in each_cluster_movies_list:
            count = 0
            missed_movies = list()
            for movie in user_movies:
                if movie in movies_list:
                    count += 1
                else:
                    missed_movies.append(movie)
            elemProbability.append(count / len(user_movies))
            user_missed_movies.append(missed_movies)
        user_new_cluster = np.array(elemProbability).argmax()
        users_cluster.loc[users_cluster['userId'] == user, 'Cluster'] = user_new_cluster
        if len(user_missed_movies[user_new_cluster]) > 0:
            loc_df = each_cluster_movies[user_new_cluster]
            for new_movie in user_missed_movies[user_new_cluster]:
                loc_df.loc[len(loc_df)] = [new_movie, 1]
            each_cluster_movies[user_new_cluster] = loc_df
    return each_cluster_movies, users_cluster
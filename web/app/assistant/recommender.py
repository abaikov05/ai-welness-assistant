from textwrap import dedent
from .helpers import openai_chat_request
from .settings import RECOMMENDATION_CATEGORIES, N_MAX_RECOMMENDATIONS
import math, heapq, json

from .settings import RECOMMENDER_DEBUG
class Data:
    """
    Data structrure with a category vector and file line number as index.
    Used in nodes in the recommendation tree.
    """
    def __init__(self, vector: list[int], index: int):
        self.vector = vector
        self.index = index
    def __str__(self):
        return f"v: {self.vector} i:{self.index}" 

class RecommerdationTree:
    """
    A KD-tree structure to store and search recommendations vectors and their indices in file.
    """
    def __init__(self, dimension: int):
        self.dimension = dimension
        self.root = None
    
    class Node:
        """
        Node in the KD-tree.
        """
        def __init__(self, data: Data=None, left: object=None, right: object=None):
            self.data = data
            self.left = left
            self.right = right
        
    def build_tree(self, data: list[Data]):
        """
        Public method to initiate the tree-building process.
        Sets the root of the KD-tree by calling the recursive helper method.
        
        Parameters:
        - data (list[Data]): A list of Data objects to build the KD-tree from.
        """
        self.root = self._build_tree(data)
        return
    
    def _build_tree(self, data: list[Data], depth=0):
        """
        Recursively builds a KD-tree from a list of Data objects.
        
        Parameters:
        - data (list[Data]): List of Data objects to insert into the tree.
        - depth (int): Current depth of the tree, used to determine the axis for splitting.
        
        Returns:
        - Node: The root Node object of the subtree for this level.
        """
        if not data:
            return None
        
        # Determine the axis to split on
        axis = depth % self.dimension
        # Sort the data by the chosen axis and find the median element.
        data.sort(key = lambda x: x.vector[axis])
        median = len(data) // 2
        
        if RECOMMENDER_DEBUG:
            for n,i in enumerate(data):
                if i == data[median]:
                    print(f"{n}: ",i, f"<{'-'*5} median")
                else:
                    print(f"{n}: ",i)
            print("Depth: ", depth,'\n',"_"*10)
        
        # Recursively build left and right subtrees, increasing the depth each time.
        return self.Node(
            data = data[median],
            left = self._build_tree(data[:median], depth + 1),
            right = self._build_tree(data[median + 1:], depth + 1)
        )

    def nearest_neighbors(self, target: list[int], n_max: int = 1):
        """
        Public method to find the nearest neighbors to a target vector in the KD-tree.
        - ! Can return less then 'n_max' neighbors if the target vector is a root of tree of close to it. !
        
        Parameters:
        - target (list[int]): The target vector for which we are finding the nearest neighbors.
        - n_max (int): The maximum number of nearest neighbors to retrieve.

        Returns:
        - list[tuple]: A list of tuples containing (distance, index, vector) with 
        maximum of `n_max` nearest neighbors.
        """
        self.nearest_heap = []
        self.n_nearest = n_max
        self._nearest_neighbors(self.root, target, 0)
        # Values in heapq are not sorted, it only ensures that min value is always at the beginning
        self.nearest_heap.sort(key=lambda x: x[0], reverse=True)
        # Return data with positive distance values
        return [(-i[0], i[1], i[2]) for i in self.nearest_heap]
    
    def _nearest_neighbors(self, node, target, depth):
        """
        Recursive helper method to perform nearest neighbor search in the KD-tree.
        
        Parameters:
        - node (Node): The current node in the KD-tree being examined.
        - target (list[int]): The target vector for which we are finding the nearest neighbors.
        - depth (int): The current depth of the node in the KD-tree, used to determine the axis for splitting.
        
        This method updates the `nearest_heap` list with the `n_max` closest neighbors to the target so returns nothing.
        """
        if node is None:
            return

        # Compute distance between target and current node's data
        current_dist = euclidean_distance(node.data.vector, target)
        
        # Fill heap until full while traversing tree 
        if len(self.nearest_heap) < self.n_nearest:
            # Add data to heap. Distance is negative because heapq is min-heap.
            # If there are equal distances, heapq compares next elements in tuple, because of that we unpack Node data here.  
            heapq.heappush(self.nearest_heap, (-current_dist, node.data.index, node.data.vector))
 
        elif current_dist <= -self.nearest_heap[0][0]:
            # Only add if current distance is closer than the farthest in the heap and remove farthest
            heapq.heappop(self.nearest_heap)
            heapq.heappush(self.nearest_heap, (-current_dist, node.data.index, node.data.vector))
            
        # Determine the axis and which side of the tree to explore
        axis = depth % self.dimension
        diff = target[axis] - node.data.vector[axis]

        # Explore the closer side of the tree first
        close_side = node.left if diff < 0 else node.right
        far_side = node.right if diff < 0 else node.left

        if RECOMMENDER_DEBUG:
            print(f"Target: {target}")
            print(f"Vector: {node.data.vector}")
            print(f"Distance: {current_dist}; Axis:{axis}; Axis diffrence:{diff}; Depth: {depth}")
            if close_side: print(f"Close side: {close_side.data.vector}")
            else: print(f"Close side: NONE")
            if far_side: print(f"Far side: {far_side.data.vector}")
            else: print(f"Far side side: NONE")
            print(f"Heap: {self.nearest_heap}")
            print('-'*10)
            
        # Recurse on the closer side
        self._nearest_neighbors(close_side, target, depth + 1)

        # If there could be a closer point on the far side, explore it
        if abs(diff) < -self.nearest_heap[0][0]:
            self._nearest_neighbors(far_side, target, depth + 1)

        return

    def serialize_tree(self):
        """
        Serializes the KD-tree to JSON format for storage.
        """
        def serialize_node(node):
            if node is None:
                return None
            return {
                'data': {
                    'vector': node.data.vector,
                    'index': node.data.index
                },
                'left': serialize_node(node.left),
                'right': serialize_node(node.right)
            }

        return serialize_node(self.root)
    
    def save_tree(self, path: str = 'web/app/assistant/Recommendations/recomendation_tree.json'):
        """
        Saves the current KD-tree to a JSON file.
        """
        with open(path, 'w') as file:
            json.dump(self.serialize_tree(), file)
    
    @staticmethod
    def deserialize_tree(data):
        """
        Deserializes JSON dictionary back into a KD-tree structure.
        """
        if data is None:
            return None

        node = RecommerdationTree.Node(
            data=Data(data['data']['vector'], data['data']['index']),
            left=RecommerdationTree.deserialize_tree(data['left']),
            right=RecommerdationTree.deserialize_tree(data['right'])
        )
        return node
    @staticmethod
    def load_tree(path: str = 'web/app/assistant/Recommendations/recomendation_tree.json'):
        """
        Loads a KD-tree from a JSON file.
        """
        if RECOMMENDER_DEBUG: print('- Loadin recommendation tree from:',path)
        with open(path, 'r') as file:
            data = json.load(file)
            tree = RecommerdationTree(len(data['data']['vector']))
            tree.root = RecommerdationTree.deserialize_tree(data)
            
        return tree
        
def euclidean_distance(point1, point2):
    dist = 0
    for i in range(len(point1)):
        dist += (point1[i] - point2[i]) ** 2
    return math.sqrt(dist)
        
class Recommender:
    """
    The Recommender class provides functionalities to manage, process, and retrieve recommendations 
    based on category vectors. It uses a KD-tree to efficiently search for similar recommendations.
    """
    def __init__(self,
                 gpt_model: str,
                 recommendations_tree_path: str='web/app/assistant/Recommendations/recomendation_tree.json',
                 recommendations_path: str="web/app/assistant/Recommendations/recommendations.txt"):
        """
        Initializes the Recommender instance with specified GPT model and paths for recommendations and tree.

        Parameters:
        - gpt_model (str): GPT model used in generating recommendations and vectors.
        - recommendations_tree_path (str): Path to save/load the KD-tree for recommendation vectors.
        - recommendations_path (str): Path to the recommendations."""
        self.gpt_model = gpt_model
        self.recommendations_path = recommendations_path
        self.recommendations_tree_path = recommendations_tree_path
        
    def build_and_save_rec_tree(self):
        """
        Builds a KD-tree from recommendations vectors and saves it for faster retrieval of similar recommendations.
        """
        recommendation_data = []
        with open(self.recommendations_path, 'r', encoding="utf-8") as file:
            for line_num, line in enumerate(file):
                vector = line.split(':', maxsplit=1)[0]
                vector = list(map(int, vector.split(',')))
                recommendation_data.append(Data(vector, line_num))
        
        dimension = len(recommendation_data[0].vector)
        
        tree = RecommerdationTree(dimension)
        tree.build_tree(recommendation_data)
        tree.save_tree(self.recommendations_tree_path)
        
        return
        
    def get_recomendations(self, target: list[int], n_max: int):
        """
        Get
        """
        # Load the recommendation tree and find nearest neighbors
        tree = RecommerdationTree.load_tree(self.recommendations_tree_path)
        nearest_data = tree.nearest_neighbors(target, n_max)
        # Sort nearest_data by line number in ascending order for efficient reading
        nearest_data.sort(key = lambda x: x[1])
        
        recommendations = []
        curent_index = 0
        # Read file and append recommendations
        with open(self.recommendations_path, 'r', encoding="utf-8") as file:
            for line_num, line in enumerate(file):
                if line_num == nearest_data[curent_index][1]:

                    text = line.split(':', maxsplit=1)[1]
                    recommendations.append((nearest_data[curent_index][0],text.split('|')))
                    
                    if curent_index >= len(nearest_data)-1:
                        break
                    curent_index += 1
        
        # Return the sorted recommendations by distance
        recommendations.sort(key = lambda x:x[0])
        return recommendations
        
    async def generate_categories_v(self, categories: list[str], text: str, max_val: int = 10):
        """
        Generates a vector of relevance scores for each category based on input text.
        
        Parameters:
        - categories (list[str]): List of categories to analyze against the text.
        - text (str): The content to be analyzed.
        - max_val (int): Maximum allowed score for each category.
        
        Returns:
        - Tuple of (response, token_usage):
        - response (list[int] or None): A list of integer scores if successful; None if an error occurs.
        - token_usage (int or None): Number of tokens used in the request.
        """
        system = dedent("""\
            You are a text analyzer that assigns a relevance score to each category based 
            on the content of a given text. Your task is to generate a vector of scores that 
            reflects how closely the text matches each category. 
            
            Input Parameters:
            - categories: A list of categories. Each category represents a dimension in the output vector.
            - max_value: The maximum possible value for any element in the vector.
            - text: The input text to analyze.
            
            Generate a vector where each element corresponds to a category in categories.
            Each element in the vector should be an integer from 0 to max_value, representing the relevance of the text to that category.
            
            Think deeply on each category.
            Your response always is only values of vector delimited by comma.
            Example output:
            1,4,5,7
            
            Remember: Always output the vector in the order provided in categories, with each element as an integer within the range [0, max_value].""")
        prompt = dedent(f"""\
            categories: {categories}
            max_value: {max_val}
            text: {text}""")
        print("GEENERATE CAT V PROMPT:", prompt, system, self.gpt_model)
        response, token_usage = await openai_chat_request(prompt=prompt, system=system, model=self.gpt_model)
        # Validate response
        if response is not None:
            try:
                response = response.split(',')
                response = list(map(int, response))
                
                if len(response) != len(categories):
                    raise Exception('Invalid length of response vector')
                
                for val in response:
                    if val > max_val or val < 0:
                        raise Exception('Invalid value in response vector')
                
                return response, token_usage
            
            except Exception as e:
                print(f"Error processing recommenders vector generation response: {str(e)}")
                return None, token_usage
        else:
            print("Error in generating categories vector")
            return None, None

    async def handle_recommendations(self, chat_history: str, distance_threshhold: int = 10):
        vector, used_tokens = await self.generate_categories_v(categories=RECOMMENDATION_CATEGORIES, text=str(chat_history))
        recommendations = self.get_recomendations(vector, N_MAX_RECOMMENDATIONS)
        
        result = []
        # Threshold
        for dist, rec in recommendations:
            if dist <= distance_threshhold:
                result.append(rec)
            else:
                break
        
        return result, used_tokens
        
        
    
    async def generate_recommendation(self, addition: str = None, vector: list[int] = None, vector_categories:list[str] = None, vector_max_val: int = None):
        """
        Utility function to generate at least some recommendations.
        Generates a health and mental well-being recommendation using the provided context or category vector.
        - addition: Optional text to guide recommendation content.
        - vector: Category scores to generate recommendation.
        - vector_categories: Names of categories of the vector.
        - vector_max_val: Maximum score in the vector.
        
        Returns:
           - Tuple with the recommendation and token usage. 
        """
        system = dedent("""\
            You are a recommendation engine focused on health and mental well-being. 
            Your task is to generate a relevant recommendation that promotes health and mental health.
            Addition text, if provided, may give additional context to guide the recommendation.
            Categories with marks could be provided to guide the recommendation.
            
            Your response is always only recommendation.
            """)
        # Initialize prompt and add optional context
        prompt = ""
        if addition:
            prompt += "Additional context: " + addition + '\n'
        if vector and vector_categories and vector_max_val:
            prompt += f"Categories with marks where {vector_max_val} is highes:\n"
            for i in list(zip(vector_categories, vector)):
                prompt += f"{i[0]}: {i[1]}\n"
                
        response, token_usage = await openai_chat_request(prompt=prompt, system=system, model=self.gpt_model)
        
        if response:
            return response, token_usage
        else:
            print("Failed to generate recommendation")
            return None, None
    def save_recomendation(self, vector: list[int], recommendation:str):
        """
        Saves a recommendation and its vector to a file. If the vector already exists, appends the recommendation to that line.
        """
        vector_str = str(vector)[1:-1].replace(' ','')
        lines = []
        duplicate = False
        # Read all lines and check for duplicates
        with open(self.recommendations_path, "r", encoding='utf-8') as file:
            for line in file:
                if line.startswith(vector_str + ":"):
                    # If vector exists, append recommendation to this line
                    line = line.strip() + '|' + recommendation + '\n'
                    duplicate = True
                lines.append(line)

        # Write back all lines if a duplicate was found
        if duplicate:
            with open(self.recommendations_path, 'w', encoding='utf-8') as file:
                file.writelines(lines)
        else:
            # Append a new recommendation if no duplicate
            with open(self.recommendations_path, 'a', encoding='utf-8') as file:
                file.write(f"{vector_str}:{recommendation}\n")

        return
            
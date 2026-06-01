import numpy


def getNormalizedVectors(vectors: numpy.ndarray) -> numpy.ndarray:
    return vectors / numpy.linalg.norm(vectors, axis=1, keepdims=True)

def cosineSimilarities(embeddings: numpy.ndarray, examples: numpy.ndarray) -> numpy.ndarray:
    return numpy.dot(getNormalizedVectors(embeddings), getNormalizedVectors(examples).T)

def softmax(x: numpy.ndarray) -> numpy.ndarray:
    x = x - x.max(axis=1, keepdims=True)   # stability: subtract row max
    e = numpy.exp(x)
    return e / e.sum(axis=1, keepdims=True)

def weightedSimilarities(embeddings: numpy.ndarray, examples: numpy.ndarray) -> numpy.ndarray:
    similarities = cosineSimilarities(embeddings, examples)
    weights = softmax(similarities)
    weighted_similarities = (weights * similarities).sum(axis=1)
    return weighted_similarities
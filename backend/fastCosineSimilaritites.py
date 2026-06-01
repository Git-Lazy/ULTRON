import numpy


def getNormalizedVectors(vectors: numpy.ndarray) -> numpy.ndarray:
    return vectors / numpy.linalg.norm(vectors, axis=1, keepdims=True)

def cosineSimilarities(embeddings: numpy.ndarray, examples: numpy.ndarray) -> float:
    return numpy.dot(getNormalizedVectors(embeddings), getNormalizedVectors(examples).T)
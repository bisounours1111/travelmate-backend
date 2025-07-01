from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import googlemaps
from datetime import datetime
import math
from enum import Enum
from fastapi import Query
import polyline
from geopy.distance import geodesic
import json

router = APIRouter()

class ActivityType(Enum):
    MONUMENT = "monument"
    PARK = "park"
    MUSEUM = "museum"
    POINT_OF_INTEREST = "point_of_interest"
    RESTAURANT = "restaurant"
    BAR = "bar"

class PertinentType(Enum):
    MONUMENT = "monument"
    MUSEUM = "museum"
    PARK = "park"
    TOURIST_ATTRACTION = "tourist_attraction"
    AMUSEMENT_PARK = "amusement_park"
    CHURCH = "church"
    CEMETERY = "cemetery"
    PLACE_OF_WORSHIP = "place_of_worship"
    ART_GALLERY = "art_gallery"
    ZOO = "zoo"
    AQUARIUM = "aquarium"
    STADIUM = "stadium"
    LIBRARY = "library"
    MOVIE_THEATER = "movie_theater"
    NIGHT_CLUB = "night_club"
    CASINO = "casino"
    BOWLING_ALLEY = "bowling_alley"
    SPA = "spa"
    RESTAURANT = "restaurant"
    CAFE = "cafe"
    BAR = "bar"
    CAMPGROUND = "campground"
    POINT_OF_INTEREST = "point_of_interest"
    NATURAL_FEATURE = "natural_feature"
    SCENIC_LOOKOUT = "scenic_lookout"
    HIKING_AREA = "hiking_area"
    BEACH = "beach"
    LAKE = "lake"
    MOUNTAIN = "mountain"
    WATER_PARK = "water_park"
    THEME_PARK = "theme_park"
    GALLERY = "gallery"
    HISTORICAL_LANDMARK = "historical_landmark"

# Configuration Google Maps (à remplacer par votre clé API)
gmaps = googlemaps.Client(key='AIzaSyDiYUpbY37NS5-UrsFCDZwawFvv4gMahjk')

TYPES_PERTINENTS = {pt.value for pt in PertinentType}

def get_points_along_route(route, num_points=10):
    """
    Calcule des points régulièrement espacés le long du trajet
    """
    points = []
    if 'legs' in route:
        for leg in route['legs']:
            if 'steps' in leg:
                for step in leg['steps']:
                    if 'polyline' in step and 'points' in step['polyline']:
                        # Décode le polyline pour obtenir les points
                        decoded_points = googlemaps.convert.decode_polyline(step['polyline']['points'])
                        points.extend(decoded_points)
    
    # Sélectionner des points régulièrement espacés
    if len(points) > num_points:
        step = len(points) // num_points
        return points[::step]
    return points

# From LAT and LON, get the closest activities
@router.get("/activities/nearby", response_model=List[Dict[str, Any]])
def get_activities_nearby(lat: float, lon: float, radius: float = 1000):
    types = json.load(open("types_activites.json"))
    types = set(types)
    """
    Recherche les activités proches d'une position donnée
    Retourne les données au format Google Maps pour Swift
    """
    try:
        # Utiliser Google Places API pour trouver les activités proches
        places_result = gmaps.places_nearby(
            location=(lat, lon),
            radius=radius,
            type=ActivityType.MONUMENT.value
        )
        
        formatted_activities = []
        print(places_result)
        if 'results' in places_result:
            for place in places_result['results']:
                types.update(place.get('types', []))

                if set(place.get('types', [])) & TYPES_PERTINENTS:
                    formatted_activity = {
                            "position": {
                                "lat": place['geometry']['location']['lat'],
                            "lng": place['geometry']['location']['lng']
                        },
                        "name": place['name'],
                        "description": place.get('vicinity', ''),
                        "category": place.get('types', ['point_of_interest'])[0],
                        "rating": place.get('rating', 0),
                        "place_id": place['place_id']
                    }

                    formatted_activities.append(formatted_activity)
        
        # À la fin, convertis le set en liste
        types_list = list(types)
        # Sauvegarde dans un fichier JSON
        with open("types_activites.json", "w", encoding="utf-8") as f:
            json.dump(types_list, f, ensure_ascii=False, indent=2)
        return formatted_activities
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# From (lat, lon) and (lat, lon) of the end point, get the route
@router.get("/routes")
def get_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float):
    route_data = {
        "start_lat": start_lat,
        "start_lon": start_lon,
        "end_lat": end_lat,
        "end_lon": end_lon
    }
    return route_data

# From (lat, lon) and (lat, lon) of the end point, get the route with the closest activities
@router.get("/routes/nearby")
def get_route_nearby(start_lat: float, start_lon: float, end_lat: float, end_lon: float):
    route_data = {
        "start_lat": start_lat,
        "start_lon": start_lon,
        "end_lat": end_lat,
        "end_lon": end_lon
    }
    return route_data

@router.get("/routes/directions", response_model=Dict[str, Any])
def get_route_directions(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    mode: str = "driving"
):
    """
    Calcule un trajet entre deux points
    Retourne les données au format Google Maps pour Swift
    """
    try:
        directions_result = gmaps.directions(
            (start_lat, start_lon),
            (end_lat, end_lon),
            mode=mode,
            departure_time=datetime.now()
        )
        
        if not directions_result:
            raise HTTPException(status_code=404, detail="Aucun itinéraire trouvé")
            
        route = directions_result[0]
        
        # Format pour Google Maps
        formatted_route = {
            "overview_polyline": route["overview_polyline"],
            "legs": [{
                "distance": leg["distance"],
                "duration": leg["duration"],
                "steps": [{
                    "polyline": step["polyline"],
                    "distance": step["distance"],
                    "duration": step["duration"]
                } for step in leg["steps"]]
            } for leg in route["legs"]]
        }
        
        return formatted_route
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def filter_best_activity(places_result, seen_place_ids):
    """
    Filtre et retourne la meilleure activité parmi les résultats
    Priorité: rating > pertinence du type > distance
    """
    if 'results' not in places_result or not places_result['results']:
        return None
    
    best_place = None
    best_score = -1
    
    for place in places_result['results']:
        if place['place_id'] in seen_place_ids:
            continue
            
        # Calculer un score basé sur le rating et la pertinence
        rating = place.get('rating', 0)
        types = set(place.get('types', []))
        
        # Score de pertinence des types (plus le type est spécifique, mieux c'est)
        type_score = 0
        if PertinentType.MUSEUM.value in types:
            type_score = 10
        elif PertinentType.MONUMENT.value in types or PertinentType.TOURIST_ATTRACTION.value in types:
            type_score = 8
        elif PertinentType.PARK.value in types or PertinentType.NATURAL_FEATURE.value in types:
            type_score = 6
        elif PertinentType.RESTAURANT.value in types or PertinentType.CAFE.value in types:
            type_score = 4
        else:
            type_score = 2
        
        # Score total (rating * 2 + type_score)
        total_score = (rating * 2) + type_score
        
        if total_score > best_score:
            best_score = total_score
            best_place = place
    
    return best_place

@router.get("/routes/nearby-activities", response_model=Dict[str, Any])
def get_route_with_nearby_activities(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    radius: float = 1000,
    mode: str = "driving"
):
    """
    Calcule un trajet et trouve les activités proches sur le trajet en utilisant Google Places
    """
    try:
        print(f"Recherche d'itinéraire de ({start_lat}, {start_lon}) à ({end_lat}, {end_lon})")
        
        # Obtenir l'itinéraire
        directions_result = gmaps.directions(
            (start_lat, start_lon),
            (end_lat, end_lon),
            mode=mode,
            departure_time=datetime.now()
        )
        
        if not directions_result:
            raise HTTPException(status_code=404, detail="Aucun itinéraire trouvé")
            
        route = directions_result[0]
        
        # Obtenir des points le long du trajet
        route_points = get_points_along_route(route)
        print(f"Nombre de points le long du trajet: {len(route_points)}")
        
        # Rechercher des points d'intérêt autour de chaque point avec pré-filtrage
        all_places = []
        seen_place_ids = set()  # Pour éviter les doublons
        
        for i, point in enumerate(route_points):
            # Recherche de points d'intérêt autour du point
            places_result = gmaps.places_nearby(
                location=(point['lat'], point['lng']),
                radius=radius,
                type=ActivityType.MONUMENT.value
            )
            
            # Pré-filtrage: ne récupérer qu'une seule activité pertinente par point
            best_place = filter_best_activity(places_result, seen_place_ids)
            
            if best_place:
                seen_place_ids.add(best_place['place_id'])
                if set(best_place.get('types', [])) & TYPES_PERTINENTS:
                    all_places.append({
                        "position": {
                            "lat": best_place['geometry']['location']['lat'],
                            "lng": best_place['geometry']['location']['lng']
                        },
                        "name": best_place['name'],
                        "description": best_place.get('vicinity', ''),
                        "category": best_place.get('types', ['point_of_interest'])[0],
                        "rating": best_place.get('rating', 0),
                        "place_id": best_place['place_id']
                    })
        
        print(f"Nombre total de points d'intérêt trouvés après filtrage: {len(all_places)}")
        
        # Format pour Google Maps
        formatted_response = {
            "route": {
                "overview_polyline": route["overview_polyline"],
                "legs": [{
                    "distance": leg["distance"],
                    "duration": leg["duration"],
                    "steps": [{
                        "polyline": step["polyline"],
                        "distance": step["distance"],
                        "duration": step["duration"]
                    } for step in leg["steps"]]
                } for leg in route["legs"]]
            },
            "nearby_activities": all_places
        }
        
        return formatted_response
        
    except Exception as e:
        print(f"Erreur: {str(e)}")  # Debug: Afficher l'erreur
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activities-along-route", response_model=Dict[str, Any])
def get_activities_along_route(
    start_lat: float = Query(...),
    start_lon: float = Query(...),
    end_lat: float = Query(...),
    end_lon: float = Query(...),
    activity_type: PertinentType = Query(...),
    radius: float = 1500,
    sampling_distance: float = 50
):
    """
    Calcule un itinéraire et trouve les activités du type spécifié le long du trajet
    """
    try:
        # Récupérer l'itinéraire
        directions_result = gmaps.directions(
            (start_lat, start_lon),
            (end_lat, end_lon),
            mode="driving"
        )

        if not directions_result:
            raise HTTPException(status_code=404, detail="Itinéraire introuvable.")

        route = directions_result[0]
        
        # Obtenir des points échantillonnés le long du trajet
        sampled_points = get_sampled_points(route, sampling_distance)
        
        # Rechercher les activités autour des points échantillonnés
        activities = find_activities_along_route(sampled_points, activity_type, radius)
        
        # Formater la réponse
        formatted_response = {
            "route": {
                "overview_polyline": route["overview_polyline"],
                "legs": [{
                    "distance": leg["distance"],
                    "duration": leg["duration"],
                    "steps": [{
                        "polyline": step["polyline"],
                        "distance": step["distance"],
                        "duration": step["duration"]
                    } for step in leg["steps"]]
                } for leg in route["legs"]]
            },
            "activities": activities
        }
        
        return formatted_response
        
    except Exception as e:
        print(f"Erreur: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def get_sampled_points(route: Dict[str, Any], sampling_distance: float) -> List[tuple]:
    """
    Échantillonne des points le long du trajet à intervalles réguliers
    """
    polyline_points = route['overview_polyline']['points']
    route_points = polyline.decode(polyline_points)
    
    sampled_points = []
    last_point = route_points[0]
    sampled_points.append(last_point)
    distance_acc = 0.0
    
    for point in route_points[1:]:
        dist = geodesic(last_point, point).kilometers
        distance_acc += dist
        if distance_acc >= sampling_distance:
            sampled_points.append(point)
            last_point = point
            distance_acc = 0.0
            
    return sampled_points

def find_activities_along_route(
    points: List[tuple],
    activity_type: ActivityType,
    radius: float
) -> List[Dict[str, Any]]:
    """
    Recherche les activités autour des points donnés avec pré-filtrage
    """
    activities = []
    seen_place_ids = set()
    
    for lat, lng in points:
        places_result = gmaps.places_nearby(
            location=(lat, lng),
            radius=radius,
            type=activity_type.value
        )
        
        # Pré-filtrage: ne récupérer qu'une seule activité pertinente par point
        best_place = filter_best_activity(places_result, seen_place_ids)
        
        if best_place:
            seen_place_ids.add(best_place['place_id'])
            if set(best_place.get('types', [])) & TYPES_PERTINENTS:
                activities.append({
                    "position": {
                        "lat": best_place['geometry']['location']['lat'],
                        "lng": best_place['geometry']['location']['lng']
                    },
                    "name": best_place['name'],
                    "description": best_place.get('vicinity', ''),
                    "category": best_place.get('types', ['point_of_interest']),
                    "rating": best_place.get('rating', 0),
                    "place_id": best_place['place_id']
                })
                
    return activities

@router.get("/address")
def find_address(address: str):
    return gmaps.geocode(address, language="fr")
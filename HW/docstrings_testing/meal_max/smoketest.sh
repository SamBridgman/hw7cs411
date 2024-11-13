#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5000/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done


###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health_status() {
  echo "Checking status"
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "It is healthy."
  else
    echo "check failed."
    exit 1
  fi
}

# Function to check the database connection
check_db() {
  echo "Checking DB connection..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"database_status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "DBCONN is healthy."
  else
    echo "DB check failed."
    exit 1
  fi
}


##########################################################
#
# Meal Management
#
##########################################################

create_meal() {
  meal=$1
  cuisine=$2
  price=$3
  difficulty=$4

  echo "Adding meal ($meal, $cuisine, $price, $difficulty) to battle..."
  response=$(curl -s -X POST "$BASE_URL/create-meal" -H "Content-Type: application/json" \
    -d "{\"meal\":\"$meal\", \"cuisine\":\"$cuisine\", \"price\":$price, \"difficulty\":\"$difficulty\"}")
  
  if echo "$response" | grep -q '"status": "success"'; then 
    echo "Meal added"
  else 
    echo "Unable to add meal"
    exit 1
  fi
}

clear_kitchen_catalog() {
  echo "Clearing the kitchen catalog..."
  curl -s -X DELETE "$BASE_URL/clear-meals" | grep -q '"status": "success"'
}

remove_meal() {
  meal_id=$1

  echo "Deleting meal by the ID ($meal_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-meal/$meal_id")
  if echo "$response" | grep -q '"status": *"success"'; then
    echo "Meal has been deleted successfully by ID ($meal_id)."
  else
    echo "Unable to delete meal with ID ($meal_id)."
    exit 1
  fi
}

get_meal_by_id() {
  meal_id=$1

  echo "Getting meal by id. ($meal_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-id/$meal_id")
  if echo "$response" | grep -q '"status": *"success"'; then
    echo "Meal received successfully by ID ($meal_id)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (ID $meal_id):"
      echo "$response" | jq .
    fi
  else
    echo "Unable to get meal by ID ($meal_id)."
    exit 1
  fi
}

get_meal_by_nameofmeal() {
  meal=$1

  echo "Getting meal by the name ($meal)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-name/$(echo $meal | sed 's/ /%20/g')")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal received successfully by name ($meal)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (Name $meal):"
      echo "$response" | jq .
    fi
  else
    echo "Unable to get meal by name ($meal)."
    exit 1
  fi
}

prepare_combatant() {
  meal=$1

  echo "Preparing combatant for battle: $meal ..."
  response=$(curl -s -X POST "$BASE_URL/prep-combatant" \
    -H "Content-Type: application/json" \
    -d "{\"meal\":\"$meal\"}")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatant has been prepped succesfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON:"
      echo "$response" | jq .
    fi
  else
    echo $response
    echo "Unable to prep combatant"
    exit 1
  fi
}

clear_combatants() {
  echo "Clearing combatants..."
  response=$(curl -s -X POST "$BASE_URL/clear-combatants")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatants removed successfully."
  else
    echo "Unable to clear combatants."
    exit 1
  fi
}

get_combatants() {  
  echo "Receiving all combatants for the battle..."
  response=$(curl -s -X GET "$BASE_URL/get-combatants")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "All combatants from battle retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Combatants JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Unable to retrieve all combatants."
    exit 1
  fi
}

battle() {
  

  echo "Entering the battle..."

  response=$(curl -s -X GET "$BASE_URL/battle")

  if echo "$response" | grep -q '"status": *"success"'; then
    echo "Battle ended successfully."
    echo "The winner of battle is "
    echo "$response" | jq .winner
  else
    echo $response
    echo "Unable to start battle."
    exit 1
  fi
}

# Function to get the song leaderboard sorted by play count
get_leaderboard() {
  ECHO_JSON=true
  sort=$1
  echo "Getting the leaderboard sorted by $sort..."
  response=$(curl -s -X GET "$BASE_URL/leaderboard?sort=$sort")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal leaderboard received successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal leaderboard JSON (sorted by $sort):"
      echo "$response" | jq .
    fi
  else
    echo $response 
    echo "Unable to get meal leaderboard."
    exit 1
  fi
}




# Health checks
check_health
check_db

# Create meals
add_meal "Meal A" "Cuisine A" 1 "LOW"
add_meal "Meal B" "Cuisine B" 2 "MED"
add_meal "Meal C" "Cuisine C" 3 "HIGH"
add_meal "Meal D" "Cuisine D" 4 "LOW"
delete_meal 3
add_meal "Meal C" "Cuisine C" 3 "HIGH"

get_meal_by_id 2
get_meal_by_name "Meal C"

clear_combatants
prep_combatant "Meal A" "Cuisine A" 1 "LOW"
prep_combatant "Meal B" "Cuisine B" 2 "MED"
get_combatants
battle

clear_combatants
prep_combatant "Meal C" "Cuisine C" 3 "MED"
prep_combatant "Meal D" "Cuisine D" 4 "MED"
get_combatants
battle

get_leaderboard 

echo "All tests passed successfully!"
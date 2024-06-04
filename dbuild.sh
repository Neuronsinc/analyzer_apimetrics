#!/bin/bash
IMAGEN="analyzer_apimetrics"
DH_USER="ojrivera"

sub=$(tput smul)
b=$(tput bold)
d=$(tput dim)
r=$(tput sgr0)


exec_build(){
  repo=`git remote -v | grep origin | head -1 | sed 's/.*\/\([^ ]*\) .*/\1/' | sed 's/\.git$//'`
  echo "${d}Se realizara el build sobre el repositorio:${r} ${b}$repo${r}"
  echo ""

  branches=(`gh api \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    /repos/Neuronsinc/$repo/branches | jq -r '.[].name'`)

  branches=($(for opcion in "${branches[@]}"; do echo "$opcion"; done | tac))
  PS3="${d}Seleccionar el issue/rama: ${r}"
  select branch in "${branches[@]}"; do
    if [ -n "$branch" ]; then

      info=`gh api \
              -H "Accept: application/vnd.github+json" \
              -H "X-GitHub-Api-Version: 2022-11-28" \
              /repos/Neuronsinc/$repo/events | jq --arg br "$branch" '.[] | select(.type == "CreateEvent" and .payload.ref == $br) .created_at'`

      echo ""

      develop_end=`gh repo view --json=pushedAt -q .pushedAt Neuronsinc/"$repo" -b "$branch"`
      # echo $develop_end

      start=$(echo "$info" | tr -d '"')
      end=$(echo "$develop_end" | tr -d '"')

      fecha_local=$(TZ="America/Bogota" date -d "$start" +"%Y-%m-%dT%H:%M:%S%:z")
      fecha_dev_end=$(TZ="America/Bogota" date -d "$end" +"%Y-%m-%dT%H:%M:%S%:z")

      COMMIT=$(git log -1 --pretty=%h)
      BUILD_TIMESTAMP=$( date '+%FT%H:%M:%S' )
      REPO="$DH_USER/$IMAGEN:"
      TAG="$REPO$COMMIT"
      LATEST="${REPO}latest"
      

      echo "${d}Resumen de la publicacion ----------------------------------------------${r}"
      echo "${d}Nombre de la rama:          ${r} ${b}$branch${r}"
      echo "${d}Fecha de inicio de la rama: ${r} ${b}$fecha_local${r}"
      echo "${d}Fecha de fin de la rama:    ${r} ${b}$fecha_dev_end${r}"
      echo "${d}El commit:                  ${r} ${b}$COMMIT${r}"
      echo "${d}Fecha del build:            ${r} ${b}$BUILD_TIMESTAMP${r}"
      echo "${d}tag de la imagen:           ${r} ${b}$TAG${r}"
      echo "${d}------------------------------------------------------------------------${r}"

      echo ""
      # echo "Desea continuar con el proceso: (S/n)"
      # read -r respuesta

      echo "¿Deseas seguir con el proceso? ${d}(S/n)${r}"
      read perform_build
      if [[ -z "$perform_build" || "$perform_build" =~ ^[SsYy]$ ]]; then
        export NODE_OPTIONS=--openssl-legacy-provider
        # yarn install
        # yarn build

        #validar el build
        #eventualmente realizar las pruebas


        docker build -t "$TAG" -t "$LATEST" --build-arg COMMIT="$COMMIT" \
                                            --build-arg TIME="$BUILD_TIMESTAMP" \
                                            --build-arg START="$fecha_local" \
                                            --build-arg DEV_END="$fecha_dev_end" \
                                            --build-arg BRANCH="$branch" . 

        docker push "$TAG" 
        docker push "$LATEST"

      else
        echo "Operación cancelada."
      fi

      break
    else
      echo "Selección no válida. Por favor, elige una opción válida."
    fi
  break
  done
}


exec_register(){
  echo "registrando el pod"
  echo $DORA_REGISTER_SERVICE_SERVICE_HOST
  echo $DORA_REGISTER_SERVICE_SERVICE_PORT

  dora_host=${DORA_REGISTER_SERVICE_SERVICE_HOST:-localhost}
  dora_port=${DORA_REGISTER_SERVICE_SERVICE_PORT:-80}

  echo $dora_host

  URL="http://${dora_host}:${dora_port}/v1/Register"
  echo $URL
  DATA="{\"develop_start\": \"$BUILD_START\", \"build_branch\": \"$BUILD_BRANCH\", \"build_commit\": \""$BUILD_COMMIT"\", \"publish_time\": \"$BUILD_TIME\", \"develop_end\": \"$DEVELOP_END\", \"publish_type\": \"$PUBLISH_TYPE\"}"
  echo $DATA
  request=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$DATA" "$URL")
  # echo $DATA > register.txt
  echo $request >> register.txt
  echo $DATA >> register.txt
  
}

if [ $# -eq 0 ]; then
    echo "Por favor, proporciona un parámetro (build o register)."
    exit 1
fi

accion=$1

case $accion in
  "build")
    echo "Ejecutando acción de construcción..."
    # Coloca aquí los comandos específicos para la acción "build"
    exec_build
    ;;
  "register")
    echo "Ejecutando acción de registro..."
    # Coloca aquí los comandos específicos para la acción "register"
    exec_register
    ;;
  *)
    echo "Parámetro no válido. Debe ser 'build' o 'register'."
    ;;
esac
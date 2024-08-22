#!/bin/bash

# Populate dependencies for all APPS projects
find /home/student/DO378/DO378-apps -name "pom.xml" \
        -not -path "./quarkus-conference/*" \
        -not -path "./quarkus-calculator/*"  \
        -not -path "./quarkus-calculator-monolith/*" \
        -not -path "./istio-tutorial/*" \
        -execdir mvn dependency:go-offline \;

# Populate dependencies for all the Quarkus CLI commands;
# Create a temporal Quarkus app
TMPDIR=$(mktemp -d)
cd "$TMPDIR" || exit 1
quarkus create app tmp -x resteasy -P io.quarkus.platform:quarkus-bom:3.8.1
cd tmp || exit 1

# Populate dependencies for the Maven Quarkus Plugin
mvn io.quarkus.platform:quarkus-maven-plugin::go-offline

# Execute quarkus commands to fetch the dependencies.
# Some commands might fail, but that's ok as long as dependencies are fetched
quarkus image build docker
quarkus image build openshift
quarkus image build jib
quarkus image build buildpack

cd ..
mvn \
io.quarkus.platform:quarkus-maven-plugin:3.8.1:create \
    -DprojectGroupId=com.redhat.training \
    -DprojectArtifactId=tenther \
    -Dextensions=resteasy \
    -DplatformVersion=3.8.1

cd tenther
mvn io.quarkus.platform:quarkus-maven-plugin::go-offline

# Cleanup Quarkus app and image.
cd ~ || exit 1
rm -rf "$TMPDIR"
podman rmi -fa

FROM ubuntu:20.04
ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
WORKDIR /home/proverif/
RUN apt-get -y update && apt-get install -y git

ENV PATH=$PATH:/home/proverif/proverif2.05

RUN apt-get install -y \
    net-tools\
    iputils-ping\
    nano\
    g++ make cmake \
    tar \
    ocaml \
    ocaml-compiler-libs \
    ocaml-findlib \
    liblablgtk2-ocaml-dev \
    wget \
    graphviz
 
RUN wget https://bblanche.gitlabpages.inria.fr/proverif/proverif2.05.tar.gz && tar -xf proverif2.05.tar.gz -C /home/proverif/ && cd /home/proverif/proverif2.05/ && ./build

FROM conv_image2
RUN cd data/pretrained && bash download_models.sh && cd ../..
RUN luarocks install loadcaffe
ADD train.sh train.sh
RUN chmod +x train.sh
ENTRYPOINT ["./train.sh"]

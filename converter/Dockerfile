FROM conv_image2
ADD train.sh train.sh
RUN chmod +x train.sh
RUN cd data/pretrained && bash download_models.sh && cd ../..
ENTRYPOINT ["./train.sh"]

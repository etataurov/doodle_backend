FROM conv_image2
ADD train.sh
RUN cd data/pretrained && bash download_models.sh && cd ../..
ENTRYPOINT ["./train.sh"]
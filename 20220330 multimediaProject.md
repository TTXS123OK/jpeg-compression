### GUI: wxPython

`pip install -U wxPython`

### tasks

#### display BMP

		1. load RGB from BMP file
		1. 调库显示

#### compress image

1. load RGB from BMP file
2. Transform RGB to YIQ and subsample color
3. compress
   1. cut image to 8*8
      1. a function to perform DCT
      2. quantilization
      3. zigzag
      4. DPCM on DC
      5. RLE on AC ()
   2. Huffman coding

4. ==write to jpeg==
5. decompress
   1. read jpeg
   2. resolve AC, DC
   3. inv zigzag
   4. inv quantilization
   5. inv DCT
   6. to YIQ
   7. YIQ to RGB



#### Questions

* 图像大小不是 8 的倍数
  * 拓展边上那一排，补成8的倍数



### todo

* 掌握 jpeg 存储格式
* wxPython 使用
* 搭框架





### reference

jpeg格式：https://www.cnblogs.com/P201821460033/p/13658489.html

详尽版：https://blog.csdn.net/yun_hen/article/details/78135122

jpeg_read: https://github.com/enmasse/jpeg_read/blob/master/jpeg_read.py

jpeg huffman code:https://zhuanlan.zhihu.com/p/72044095

jpeg 解码：https://www.jianshu.com/p/c4ab7f92d0e1




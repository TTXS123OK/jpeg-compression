| state              | UNLOADED   | LOADED          | COMPRESSING   | COMPRESSED            |
| ------------------ | ---------- | --------------- | ------------- | --------------------- |
| Select BMP File    | **LOADED** | ❌               | ❌             | ❌                     |
| Compress           | ❌          | **COMPRESSING** | Waiting       | ❌                     |
| Save JPED          | ❌          | ❌               | ❌             | **COMPRESSED**        |
| Clear All          | ❌          | **UNLOADED**    | ❌             | **UNLOADED**          |
| Compress Ratio     | Unknown    | Unknown         | Unknown       | Show                  |
| Cancel Compression | ❌          | ❌               | **LOADED**    | **LOADED**            |
| ImgFrame           | None       | BMP             | BMP + loading | BMP + arrow + loading |



### MVC model

* Model: response to Control's request and notice View to update
* View: update according the state of model and call Control when event triggered
* Control: do some control function to manipulate model


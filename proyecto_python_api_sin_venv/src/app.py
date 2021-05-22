from operator import methodcaller
from flask import Flask
from flask_pymongo import PyMongo
import traceback
from flask import Flask, request, jsonify, render_template, Response, redirect , url_for, session
import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.axes
import matplotlib.gridspec as gridspec
import json
import tinymongo as tm
import tinydb
from datetime import date, datetime

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/myDatabase"
mongo = PyMongo(app)

# Bug: https://github.com/schapman1974/tinymongo/issues/58
class TinyMongoClient(tm.TinyMongoClient):
    @property
    def _storage(self):
        return tinydb.storages.JSONStorage

db_name = 'data_base'   
db_name2 = "ventas"
add_cuantity = False

#inicio
@app.route("/")
def home():
    try:
        return render_template('home.html')
    except:
        return jsonify({'trace': traceback.format_exc()})

#función para limpiar las bases de datos
def clear():
    conn = TinyMongoClient()
    db = conn[db_name]

    db.data.remove({})

    conn.close()  

    conn2 = TinyMongoClient()
    db2 = conn2[db_name2]

    db2.data.remove({})

    conn2.close()  

#funcion para ingresar productos a la base de datos
@app.route("/ingresar", methods = ['GET', 'POST'])
def ingresar():

    #returna el cuestionario
    if request.method == "GET":
      try:
        return render_template("insert.html")
      except:
        return jsonify({'trace': traceback.format_exc()})
    

    if request.method == "POST":
        conn = TinyMongoClient()
        db = conn[db_name]

        print("ingresar")
        codigo_producto = str(request.form.get('codigo'))
        global producto
        producto = db.data.find_one({"codigo" : codigo_producto})
        descripcion = str(request.form.get('descripcion'))
        global cantidad
        cantidad = str(request.form.get('cantidad'))
        peso_individual = str(request.form.get('peso_individual'))

        #pregunta si hay un producto con el mismo codigo ingresado en la base de datos
        if producto:
            #si lo hay returna una pagina que le pregunta al cliente si desea ingresar la cantidad deseada al stock de la base de datos
            conn.close()
            try:
              return render_template("codigo_existente.html", producto=producto, cantidad=cantidad)
            except:
              return jsonify({'trace': traceback.format_exc()})
        else:
            # si no lo hay guarda los datos del producto en la base de datos y returna un mensaje de que se guardó con exito
            dato = {"codigo": codigo_producto, "cantidad": cantidad, "peso_individual": peso_individual, "descripcion": descripcion}
            db.data.insert_one(dato)
            texto = "se ha insertado tu producto correctamente en la base de datos"
            conn.close()
            try:
                return render_template("message.html", texto=texto)
            except:
                return jsonify({'trace': traceback.format_exc()})    
            
# funcion que guarda los datos del producto en la base de datos si hay un codigo ya existente
@app.route("/codigo_existente", methods = ['POST'])
def codigo_existente():
    if request.method == "POST":
        try:
            conn = TinyMongoClient()
            db = conn[db_name]

            global producto
            global cantidad
            nueva_cantidad = int(producto["cantidad"]) + int(cantidad)
            db.data.update_one({"codigo": producto["codigo"]}, {"codigo": producto["codigo"], "cantidad": str(nueva_cantidad), "peso_individual": producto["peso_individual"], "descripcion": producto["descripcion"]})
            texto = "se ha guardado el producto correctamente"
            return render_template("message.html", texto=texto)
        except:
            return jsonify({'trace': traceback.format_exc()})

#funcion para retirar stock de la base de datos
@app.route("/retirar", methods = ['GET', 'POST'])
def retirar():
    #returna el cuestionario
    if request.method == "GET":
      try:
        return render_template("retirar.html")
      except:
        return jsonify({'trace': traceback.format_exc()})

    if request.method == "POST":
        conn = TinyMongoClient()
        db = conn[db_name]

        print("ingresar")
        codigo_producto = str(request.form.get('codigo'))
        producto = db.data.find_one({"codigo" : codigo_producto})
        cantidad = str(request.form.get('cantidad'))
        #se busca en la base de datos al producto que tenga el codigo ingresado
        if producto:
            #si hay un producto con ese codigo...
            cantidad_retirada = float(cantidad) / float(producto["peso_individual"])
            if cantidad_retirada < float(producto["cantidad"]):
                #se verifica que la cantidad que se quiere retirar no sea mayor a la que esta en stock
                conn2 = TinyMongoClient()
                db2 = conn2[db_name2]
                product_code = int(producto["codigo"])
                #se guarda la cantidad que se retiro junto con los demas datos del producto y la fecha de la compra en la base de datos
                db2.data.insert_one({"codigo": product_code, "cantidad": cantidad_retirada, "peso_individual": producto["peso_individual"], "descripcion": producto["descripcion"], "fecha": datetime.now().timestamp()})
                nueva_cantidad = float(producto["cantidad"]) - cantidad_retirada
                db.data.update_one({"codigo": producto["codigo"]}, {"codigo": producto["codigo"], "cantidad": str(nueva_cantidad), "peso_individual": producto["peso_individual"], "descripcion": producto["descripcion"]})
                texto = "usted retiró", str(cantidad_retirada), str(producto["descripcion"])
                conn2.close() 
                try:
                    return render_template("message.html", texto=texto)
                except:
                    return jsonify({'trace': traceback.format_exc()})    
            else:
                #si la cantidad que se quiere retirar es mayor a la que esta en stock se returna un error
                texto = "no hay suficiente stock"
                try:
                    return render_template("error.html", texto=texto)
                except:
                    return jsonify({'trace': traceback.format_exc()})    
        else:
            #si en la base de datos no existe un producto con ese codigo se returna error
            texto = "codigo no existente"
            conn.close()
            try:
                return render_template("error.html", texto=texto)
            except:
                return jsonify({'trace': traceback.format_exc()})

#funcion para graficar
def graficar(x, y):
    fig = plt.figure()
    ax = fig.add_subplot()
    ax.plot(x, y, c='darkred', marker='^', ms=10, label='ventas')
    fig.suptitle('ventas')
    ax.legend()
    ax.grid()

    plt.plot()
    plt.show()

#funcion que busca todas las ventas con el nombre y fecha especificadas
@app.route("/search", methods = ['GET', 'POST'])
def search():

    #returna el cuestionario
    if request.method == "GET":
      try:
        return render_template("search.html")
      except:
        return jsonify({'trace': traceback.format_exc()})

    if request.method == "POST":

        conn2 = TinyMongoClient()
        db2 = conn2[db_name2]
        producto = str(request.form.get('descripcion'))
        print("que fecha desea graficar? (si quiere graficar las ventas de un dia, coloque la fecha completa, si desea hacerlo con un mes, ponga el mes. el año y deje incompleto el dia, y si desea graficar un año, coloque solo el año).")
        
        year = str(request.form.get('year'))
        mes = str(request.form.get('month'))
        dia = str(request.form.get('day'))
        producto_grafico = db2.data.find({"descripcion": producto.lower()})
        x = []
        y = []
        lista2 = []
        lista = list(producto_grafico)
        filtro = ""
        #verifica si el usuario ingreso el año, o el año y el mes, o el año el mes y el dia.
        for i in lista:
            date_time = datetime.fromtimestamp(i["fecha"])
            if mes == "" and date_time.year == int(year):
                lista2.append({"cantidad": i["cantidad"], "descripcion": i["descripcion"], "fecha": datetime.fromtimestamp(i["fecha"])})
                print("no hay mes")
                filtro = "%Y, %m"
            elif dia == "" and date_time.year == int(year) and date_time.month == int(mes):
                lista2.append({"cantidad": i["cantidad"], "descripcion": i["descripcion"], "fecha": datetime.fromtimestamp(i["fecha"])})
                print("no hay dia")
                print(date_time)
                filtro = "%Y, %m, %d"
            elif date_time.year == int(year) and date_time.month == int(mes) and date_time.day == int(dia):
                lista2.append({"cantidad": i["cantidad"], "descripcion": i["descripcion"], "fecha": datetime.fromtimestamp(i["fecha"])})
                print("esta todo puesto bro")
                filtro = "%Y, %m, %d, %H, %M, %S"

        lista2.sort(key=lambda x: x['fecha'])
        print(lista2)

        value = None
        suma = 0
        sumas = []
        contador = 0
        for i in lista2:
            contador += 1
            if filtro == "%Y, %m, %d, %H, %M, %S":
                x.append(i["fecha"])
                y.append(i["cantidad"])
            else:
                if contador == len(lista2):
                    if i["fecha"].strftime(filtro) == value.strftime(filtro):
                        print("this was true")
                        suma += i["cantidad"]
                        x.append(value)
                        y.append(suma)
                    else:
                        print("this other was")
                        value = i["fecha"]
                        suma = i["cantidad"]
                        x.append(value)
                        y.append(suma)
                elif value == None:
                    value = i["fecha"]
                    suma = i["cantidad"]
                elif i["fecha"].strftime(filtro) > value.strftime(filtro):
                    x.append(value)
                    y.append(suma)
                    value = i["fecha"]
                    suma = i["cantidad"]
                elif i["fecha"].strftime(filtro) == value.strftime(filtro):
                    suma += i["cantidad"]
        print(x)
        print(y)
        #se grafica
        graficar(x, y)
        conn2.close() 
        try:
            return render_template("home.html")
        except:
            return jsonify({'trace': traceback.format_exc()})    
     
#esta funcion sirve para randomizar datos para llenar la base de datos
def datatime_randomizer():
    conn2 = TinyMongoClient()
    db2 = conn2[db_name2]
    contador = 0
    while True:
        codigo = contador + 1
        cantidad = random.randrange(10, 1000)
        peso_individual = random.uniform(0.1, 1)
        descripcion_aleatorio = random.randrange(1, 3)
        if descripcion_aleatorio == 1:
            descripcion = "tornillos"
        else:
            descripcion = "clavos"

        ahora = datetime.now()
        year = random.randrange(2019, int(ahora.strftime('%Y')) + 1)
        if year == int(ahora.strftime('%Y')):
            month = random.randrange(1, int(ahora.strftime('%m')) + 1)
        else:
            month = random.randrange(1, 13)
        
        if month == int(ahora.strftime('%m')):
            day = random.randrange(1, int(ahora.strftime('%d')))
        else:
            if month == 1 or month == 3 or month == 5 or month == 7 or month == 8 or month == 10 or month == 12:
                day = random.randrange(1, 31)
            elif month == 4 or month == 6 or month == 9 or month == 11:
                day = random.randrange(1, 30)
            else:
                day = random.randrange(1, 28)

        hour = random.randrange(8, 18)
        minutes = random.randrange(0, 60)
        seconds = random.randrange(0, 60)
        time = datetime(year, month, day, hour, minutes, seconds)

        timestamp = datetime.timestamp(time)
        print("timestamp =", timestamp)
        print(time)
        
        db2.data.insert_one({"codigo": codigo, "cantidad": cantidad, "peso_individual": "{:.1f}".format(peso_individual) , "descripcion": descripcion, "fecha": timestamp})

        contador += 1
        if contador == 3000:
            break
    conn2.close() 

if __name__ == "__main__":
    app.run(debug=True)
    # Borrar DB
    #search()
    #datatime_randomizer()
    #clear()
    #fill()
    #question()
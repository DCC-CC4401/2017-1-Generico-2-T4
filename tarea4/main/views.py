# -*- coding: utf-8 -*-

import datetime
from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils import timezone
from .forms import LoginForm
from .forms import GestionProductosForm
from .forms import editarProductosForm
from .models import Cliente
from .models import Comida

from .models import Imagen
from .models import Transacciones
from django.db.models import Count
from django.db.models import Sum
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
import simplejson
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from multiselectfield import MultiSelectField
from django.core.files.storage import default_storage
from django.contrib.auth.models import User , Group
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.core.urlresolvers import reverse


def index(request):
    if request.session.has_key('id'):
        email = request.session['email']
        tipo = request.session['tipo']
        id = request.session['id']
        nombre =request.session['nombre']
        avatar = request.session['avatar']
        vendedores = []
        listaDeProductos = []
        formasDePago = []
        user = User.objects.get(email=email)
        url = ''
        horarioIni = 0
        horarioFin = 0
        contraseña = ''
        activo = False
        # si son vendedores, crear lista de productos
        for p in Cliente.objects.all():
            if p.tipo == 2 or p.tipo == 3:
                vendedores.append(p.user.username)
        vendedoresJson = simplejson.dumps(vendedores)
        # obtener alimentos en caso de que sea vendedor fijo o ambulante
        if tipo == 2 or tipo == 3:
            i = 0
            for producto in Comida.objects.filter(vendedor=user.cliente):
                listaDeProductos.append([])
                listaDeProductos[i].append(producto.nombre)
                categoria = str(producto.categorias)
                listaDeProductos[i].append(categoria)
                listaDeProductos[i].append(producto.stock)
                listaDeProductos[i].append(producto.precio)
                listaDeProductos[i].append(producto.descripcion)
                listaDeProductos[i].append(str(producto.imagen))
                i += 1

        listaDeProductos = simplejson.dumps(listaDeProductos, ensure_ascii=False).encode('utf8')

        # limpiar argumentos de salida segun tipo de vista
        argumentos = {"email": email, "tipo": tipo, "id": id, "vendedores": vendedoresJson, "nombre": nombre,
                      "horarioIni": horarioIni, "horarioFin": horarioFin, "avatar": avatar,
                      "listaDeProductos": listaDeProductos}
        if (tipo == 0):
            id = user.id
            tipo = user.cliente.tipo
            encontrado = True
            avatar = user.cliente.avatar
            url = 'main/baseAdmin.html'
            request.session['contraseña'] = contraseña
            return adminPOST(id, avatar, email, nombre, contraseña, request)
        if (tipo == 1):
            id = user.id
            avatar = user.cliente.avatar
            tipo = user.cliente.tipo
            encontrado = True
            avatar = user.cliente.avatar
            argumentos = {"nombresesion": nombre, "tipo": tipo, "id": id,
                          "vendedores": Cliente.objects.filter(tipo__gt=1), "avatarSesion": avatar}
            return redirect('vendorMap')
        if (tipo == 2):
            id = user.id
            tipo = user.cliente.tipo
            encontrado = True
            horarioIni = user.cliente.horarioIni
            horarioFin = user.cliente.horarioFin
            request.session['horarioIni'] = horarioIni
            request.session['horarioFin'] = horarioFin
            avatar = user.cliente.avatar
            activo = user.cliente.activo
            formasDePago = user.cliente.formasDePago
            request.session['formasDePago'] = formasDePago
            request.session['activo'] = activo
            request.session['listaDeProductos'] = str(listaDeProductos)
            request.session['favoritos'] = obtenerFavoritos(id)
            argumentos = {"nombre": nombre, "tipo": tipo, "id": id, "horarioIni": horarioIni,
                          "favoritos": obtenerFavoritos(id), "horarioFin": horarioFin, "avatar": avatar,
                          "listaDeProductos": listaDeProductos, "activo": activo, "formasDePago": formasDePago,
                          "activo": activo}
            url = 'main/vendedor-fijo.html'
        if (tipo == 3):
            id = user.id
            tipo = user.cliente.tipo
            encontrado = True
            avatar = user.cliente.avatar
            activo = user.cliente.activo
            formasDePago = user.cliente.formasDePago
            request.session['formasDePago'] = formasDePago
            request.session['activo'] = activo
            request.session['listaDeProductos'] = str(listaDeProductos)
            request.session['favoritos'] = obtenerFavoritos(id)
            argumentos = {"nombre": nombre, "tipo": tipo, "id": id, "avatar": avatar, "favoritos": obtenerFavoritos(id),
                          "listaDeProductos": listaDeProductos, "activo": activo, "formasDePago": formasDePago}
            url = 'main/vendedor-ambulante.html'

        # enviar a vista respectiva de usuario
        return render(request, url, argumentos)
    else:
        return redirect('vendorMap')

def vendorMap(request):
    vendedores=[]
    #vendedoresJson = simplejson.dumps(vendedores)
    #actualizar vendedores fijos
    for p in Cliente.objects.all():
        if p.tipo == 2:
            hi = p.horarioIni
            hf = p.horarioFin
            horai = hi[:2]
            horaf = hf[:2]
            mini = hi[3:5]
            minf = hf[3:5]
            print(datetime.datetime.now().time())
            tiempo = str(datetime.datetime.now().time())
            print(tiempo)
            hora = tiempo[:2]
            minutos = tiempo[3:5]
            estado = ""
            if horaf >= hora and hora >= horai:
                if horai == hora:
                    if minf >= minutos and minutos >= mini:
                        estado = "activo"
                    else:
                        estado = "inactivo"
                elif horaf == hora:
                    if minf >= minutos and minutos >= mini:
                        estado = "activo"
                    else:
                        estado = "inactivo"
                else:
                    estado = "activo"
            else:
                estado = "inactivo"
            if estado == "activo":
                Cliente.objects.filter(user = p).update(activo=1)
            else:
                Cliente.objects.filter(user = p).update(activo=0)
    for p in Cliente.objects.all():
        if p.tipo == 2 or p.tipo == 3:
            if p.activo:
                for prod in Comida.objects.filter(vendedor=p):
                    if prod.stock > 0:
                        vendedores.append(p)
                        break
    #vendedoresJson = simplejson.dumps(vendedores)
    #print(vendedoresJson)
    return render(request, 'main/index.html', {"vendedores": vendedores})

def loginuser(request):
    if request.session.has_key('error'):
        error = request.session['error']
        request.session['error'] = {}
    else:
        error = {}
    return render(request, 'main/login.html', error)

def fijoDashboard(request):
    print(request.POST)
    id = request.POST.get("fijoId")
    #id = str(id)
    #transacciones hechas por hoy
    transaccionesDiarias=Transacciones.objects.filter(idVendedor=id).values('fecha').annotate(conteo=Count('fecha'))
    temp_transaccionesDiarias = list(transaccionesDiarias)
    transaccionesDiariasArr = []
    for element in temp_transaccionesDiarias:
        aux = []
        aux.append(element['fecha'])
        aux.append(element['conteo'])
        transaccionesDiariasArr.append(aux)
    transaccionesDiariasArr=simplejson.dumps(transaccionesDiariasArr)
    #print(transaccionesDiariasArr)
    #ganancias de hoy
    gananciasDiarias = Transacciones.objects.filter(idVendedor=id).values('fecha').annotate(ganancia=Sum('precio'))
    temp_gananciasDiarias = list(gananciasDiarias)
    gananciasDiariasArr = []
    for element in temp_gananciasDiarias:
        aux = []
        aux.append(element['fecha'])
        aux.append(element['ganancia'])
        #print("AUX")
        #print(aux)
        gananciasDiariasArr.append(aux)
    gananciasDiariasArr = simplejson.dumps(gananciasDiariasArr)
    #print(gananciasDiariasArr)


    #todos los productos del vendedor
    productos = Comida.objects.filter(idVendedor=id).values('nombre','precio')
    temp_productos = list(productos)
    productosArr = []
    productosPrecioArr = []
    for element in temp_productos:
        aux = []
        productosArr.append(element['nombre'])
        aux.append(element['nombre'])
        aux.append(element['precio'])
        productosPrecioArr.append(aux)
    productosArr = simplejson.dumps(productosArr)
    productosPrecioArr = simplejson.dumps(productosPrecioArr)
    print(productosPrecioArr)

    #productos vendidos hoy con su cantidad respectiva
    fechaHoy = str(timezone.now()).split(' ', 1)[0]
    productosHoy = Transacciones.objects.filter(idVendedor=id,fecha=fechaHoy).values('nombreComida').annotate(conteo=Count('nombreComida'))
    temp_productosHoy = list(productosHoy)
    productosHoyArr = []
    for element in temp_productosHoy:
        aux = []
        aux.append(element['nombreComida'])
        aux.append(element['conteo'])
        productosHoyArr.append(aux)
    productosHoyArr = simplejson.dumps(productosHoyArr)
    #print(productosHoyArr)


    return render(request, 'main/fijoDashboard.html', {"transacciones":transaccionesDiariasArr,"ganancias":gananciasDiariasArr,"productos":productosArr,"productosHoy":productosHoyArr,"productosPrecio":productosPrecioArr})

def ambulanteDashboard(request):
    print(request.POST)
    id = request.POST.get("ambulanteId")
    #id = str(id)
    #transacciones hechas por hoy
    transaccionesDiarias=Transacciones.objects.filter(idVendedor=id).values('fecha').annotate(conteo=Count('fecha'))
    temp_transaccionesDiarias = list(transaccionesDiarias)
    transaccionesDiariasArr = []
    for element in temp_transaccionesDiarias:
        aux = []
        aux.append(element['fecha'])
        aux.append(element['conteo'])
        transaccionesDiariasArr.append(aux)
    transaccionesDiariasArr=simplejson.dumps(transaccionesDiariasArr)
    #print(transaccionesDiariasArr)
    #ganancias de hoy
    gananciasDiarias = Transacciones.objects.filter(idVendedor=id).values('fecha').annotate(ganancia=Sum('precio'))
    temp_gananciasDiarias = list(gananciasDiarias)
    gananciasDiariasArr = []
    for element in temp_gananciasDiarias:
        aux = []
        aux.append(element['fecha'])
        aux.append(element['ganancia'])
        #print("AUX")
        #print(aux)
        gananciasDiariasArr.append(aux)
    gananciasDiariasArr = simplejson.dumps(gananciasDiariasArr)
    #print(gananciasDiariasArr)
    #todos los productos del vendedor
    productos = Comida.objects.filter(idVendedor=id).values('nombre','precio')
    temp_productos = list(productos)
    productosArr = []
    productosPrecioArr = []
    for element in temp_productos:
        aux = []
        productosArr.append(element['nombre'])
        aux.append(element['nombre'])
        aux.append(element['precio'])
        productosPrecioArr.append(aux)
    productosArr = simplejson.dumps(productosArr)
    productosPrecioArr = simplejson.dumps(productosPrecioArr)
    print(productosPrecioArr)
    #productos vendidos hoy con su cantidad respectiva
    fechaHoy = str(timezone.now()).split(' ', 1)[0]
    productosHoy = Transacciones.objects.filter(idVendedor=id,fecha=fechaHoy).values('nombreComida').annotate(conteo=Count('nombreComida'))
    temp_productosHoy = list(productosHoy)
    productosHoyArr = []
    for element in temp_productosHoy:
        aux = []
        aux.append(element['nombreComida'])
        aux.append(element['conteo'])
        productosHoyArr.append(aux)
    productosHoyArr = simplejson.dumps(productosHoyArr)
    #print(productosHoyArr)
    return render(request, 'main/ambulanteDashboard.html', {"transacciones":transaccionesDiariasArr,"ganancias":gananciasDiariasArr,"productos":productosArr,"productosHoy":productosHoyArr,"productosPrecio":productosPrecioArr})


def adminEdit(request):
    print(request.POST)
    nombre = request.POST.get("adminName")
    print(nombre)
    contraseña = request.POST.get("adminPassword")
    print(contraseña)
    id = request.POST.get("adminId")
    print(id)
    email = request.POST.get("adminEmail")
    print(email)
    avatar = request.POST.get("adminAvatar")
    print(avatar)
    return render(request, 'main/adminEdit.html', {"nombre" : nombre,"contraseña":contraseña,"id":id,"email":email,"avatar":avatar})

def signup(request):
    return render(request, 'main/signup.html', {})

def signupAdmin(request):
    return render(request, 'main/signupAdmin.html', {})

def loggedin(request):
    return render(request, 'main/loggedin.html', {})

def loginAdmin(request):
    print("POST: ")
    print(request.POST)
    id = request.POST.get("userID")
    email = request.POST.get("email")
    avatar = "avatars/"+request.POST.get("fileName")
    nombre = request.POST.get("name")
    contraseña = request.POST.get("password")
    return adminPOST(id,avatar,email,nombre,contraseña,request)

def adminPOST(id,avatar,email,nombre,contraseña,request):
    #ids de todos los usuarios no admins
    datosClientes = []
    i = 0
    numeroClientes= Cliente.objects.count()
    numeroDeComidas = Comida.objects.count()
    for usr in Cliente.objects.raw('SELECT * FROM usuario WHERE tipo != 0'):
        datosClientes.append([])
        datosClientes[i].append(usr.id)
        datosClientes[i].append(usr.username)
        datosClientes[i].append(usr.email)
        datosClientes[i].append(usr.tipo)
        datosClientes[i].append(str(usr.avatar))
        datosClientes[i].append(usr.activo)
        datosClientes[i].append(usr.formasDePago)
        datosClientes[i].append(usr.horarioIni)
        datosClientes[i].append(usr.horarioFin)
        datosClientes[i].append(usr.contraseña)
        i += 1
    listaDeClientes = simplejson.dumps(datosClientes, ensure_ascii=False).encode('utf8')
    # limpiar argumentos de salida segun tipo de vista
    argumentos = {"nombre":nombre,"id":id,"avatar":avatar,"email":email,"lista":listaDeClientes,"numeroClientes":i,"numeroDeComidas":numeroDeComidas,"contraseña":contraseña}
    return render(request, 'main/baseAdmin.html', argumentos)


def obtenerFavoritos(idVendedor):
    favoritos = 0
    user = get_object_or_404(User, id=idVendedor)
    for fila in user.cliente.favoritos.all():
        favoritos += 1
    return favoritos


def loginReq(request):
    if request.session.has_key('email'):
        email = request.session['email']
        password = request.session['password']
        try:
            name = User.objects.get(email=email).username
        except User.DoesNotExist:
            request.session['error'] = {"error": "Cliente o contraseña invalidos"}
            return redirect('login')
    else:
        email = request.POST.get("email")
        password = request.POST.get("password")
    # buscar vendedor en base de datos
        MyLoginForm = LoginForm(request.POST)
        if MyLoginForm.is_valid():
            try:
                name = User.objects.get(email=email).username
            except User.DoesNotExist:
                request.session['error'] = {"error": "Cliente o contraseña invalidos"}
                return redirect('login')
    encontrado = False
    user = authenticate(username=name, password=password)
    if user is not None:
        login(request, user)
        tipo = user.cliente.tipo
        nombre = user.username
        if (tipo == 0):
            url = 'main/baseAdmin.html'
            id = user.id
            tipo = user.cliente.tipo
            encontrado = True
            avatar = user.cliente.avatar
            contraseña = password
        elif (tipo == 1):
            url = 'main/index.html'
            id = user.id
            avatar = user.cliente.avatar
            tipo = user.cliente.tipo
            encontrado = True
            avatar = user.cliente.avatar
        elif (tipo == 2):
            url = 'main/vendedor-fijo.html'
            id = user.id
            tipo = user.cliente.tipo
            encontrado = True
            horarioIni = user.cliente.horarioIni
            horarioFin = user.cliente.horarioFin
            request.session['horarioIni'] = horarioIni
            request.session['horarioFin'] = horarioFin
            avatar = user.cliente.avatar
            activo = user.cliente.activo
            formasDePago = user.cliente.formasDePago
            request.session['formasDePago'] = formasDePago
            request.session['activo'] = activo
        elif (tipo == 3):
            url = 'main/vendedor-ambulante.html'
            id = user.id
            tipo = user.cliente.tipo
            encontrado = True
            avatar = user.cliente.avatar
            activo = user.cliente.activo
            formasDePago = user.cliente.formasDePago
            request.session['formasDePago'] = formasDePago
            request.session['activo'] = activo
        # si no se encuentra el usuario, se retorna a pagina de login
    elif encontrado == False:
        request.session['error'] = {"error": "Cliente o contraseña invalidos"}
        return redirect('login')
        # crear datos de sesion
    request.session['id'] = id
    request.session['tipo'] = tipo
    request.session['email'] = email
    request.session['nombre'] = nombre
    request.session['avatar'] = str(avatar)

    return redirect('index')



def gestionproductos(request):
    if request.session.has_key('id'):
        email = request.session['email']
        tipo = request.session['tipo']
        id = request.session['id']
        if tipo == 3:
            path = "main/index.html"
        if tipo == 2:
            path = "main/index.html"
    return render(request, 'main/agregar-productos.html', {"path" : path})

def vendedorprofilepage(request):
    return render(request, 'main/vendedor-profile-page.html', {})

def logout_intent(request):
    logout(request)
    return index(request)

def register(request):
    tipo = request.POST.get("tipo")
    nombre = request.POST.get("nombre")
    email = request.POST.get("email")
    password = request.POST.get("password")
    horaInicial = request.POST.get("horaIni")
    horaFinal = request.POST.get("horaFin")
    avatar = request.FILES.get("avatar")
    formasDePago =[]
    if not (request.POST.get("formaDePago0") is None):
        formasDePago.append(request.POST.get("formaDePago0"))
    if not (request.POST.get("formaDePago1") is None):
        formasDePago.append(request.POST.get("formaDePago1"))
    if not (request.POST.get("formaDePago2") is None):
        formasDePago.append(request.POST.get("formaDePago2"))
    if not (request.POST.get("formaDePago3") is None):
        formasDePago.append(request.POST.get("formaDePago3"))
    us = User( username = nombre, email = email)
    us.set_password(password)
    us.save()
    usuarioNuevo = Cliente.objects.create(user =us ,tipo=tipo,avatar=avatar,formasDePago=formasDePago,horarioIni=horaInicial,horarioFin=horaFinal)
    usuarioNuevo.save()
    request.session['nombre'] = nombre
    request.session['password'] = password
    request.session['email'] = email
    return redirect('loginReq')

def productoReq(request):
    horarioIni = 0
    horarioFin = 0
    avatar = ""
    if request.method == "POST":
        if request.session.has_key('id'):
            sid = request.session['id']
            email = request.session['email']
            tipo = request.session['tipo']
            if tipo == 3:
                path = "main/index.html"
                url ="main/vendedor-ambulante.html"
            if tipo == 2:
                path = "main/index.html"
                url = "main/vendedor-fijo.html"
            Formulario = GestionProductosForm(request.POST)
            if Formulario.is_valid():
                producto = Comida()
                producto.vendedor = Cliente.objects.get(user=User.objects.get(id=sid))
                producto.nombre = request.POST.get("nombre")
                producto.imagen = request.FILES.get("comida")
                producto.precio = request.POST.get("precio")
                producto.stock = request.POST.get("stock")
                producto.descripcion = request.POST.get("descripcion")
                producto.categorias = request.POST.get("categoria")
                producto.save()
            else:
                return render(request, 'main/agregar-productos.html', {"path" : path, "respuesta": "¡Ingrese todos los datos!"})
    return redirect('index')

def vistaVendedorPorAlumno(request, nombre_vendedor):
    
    user = get_object_or_404(User, username=nombre_vendedor)
    productos = Comida.objects.filter(vendedor=user.cliente)
            
    favorito = 0
    if 'id'  in request.session:
        

        alumno = get_object_or_404(User, id=request.session['id'])

        for f in alumno.cliente.favoritos.all():
            if f.user.username == nombre_vendedor:
        
                favorito = 1
        avatarSesion = request.session['avatar']
    tipo = user.cliente.tipo
    activo = user.cliente.activo
    nombre = user.username
    avatar = user.cliente.avatar
    formasDePago = user.cliente.formasDePago
    horarioIni = user.cliente.horarioIni
    horarioFin = user.cliente.horarioFin
    if(user.cliente.tipo==2):
        now = timezone.now()
        if(horarioFin>now and horarioIni<now ):
            activo = True
        else:
            activo = False
    url = 'main/vendedor-ambulante-vistaAlumno.html'
    
            
    # obtener alimentos
    i = 0
    listaDeProductos = []
    for producto in productos:
        listaDeProductos.append([])
        listaDeProductos[i].append(producto.nombre)
        categoria = str(producto.categorias)
        listaDeProductos[i].append(categoria)
        listaDeProductos[i].append(producto.stock)
        listaDeProductos[i].append(producto.precio)
        listaDeProductos[i].append(producto.descripcion)
        listaDeProductos[i].append(str(producto.imagen))
        i += 1
    
    listaDeProductos = simplejson.dumps(listaDeProductos, ensure_ascii=False).encode('utf8')
    

    if 'id'  in request.session:

        return render(request, url, {"activo": activo, "nombre": nombre, "nombresesion":request.session['nombre'], "tipo": tipo, "id": id, "avatar" : avatar, "listaDeProductos" :listaDeProductos,"avatarSesion": avatarSesion,"favorito": favorito, "formasDePago": formasDePago, "horarioIni": horarioIni, "horarioFin" : horarioFin, })
    else:

        return render(request, url, {"activo": activo , "tipo": tipo, "id": id, "listaDeProductos" :listaDeProductos, "avatar" : avatar, "formasDePago": formasDePago, "horarioIni": horarioIni, "horarioFin" : horarioFin, })




@csrf_exempt
def editarVendedor(request):
    if request.session.has_key('id'):
        id = request.session['id']
        nombre = request.session['nombre']
        formasDePago = request.session['formasDePago']
        avatar = request.session['avatar']
        tipo = request.session['tipo']
        activo = request.session['activo']
        listaDeProductos = request.session['listaDeProductos']
        favoritos = request.session['favoritos']
        if (tipo == 2):
            horarioIni = request.session['horarioIni']
            horarioFin = request.session['horarioFin']
            argumentos = {"nombre": nombre, "tipo": tipo, "id": id, "horarioIni": horarioIni, "horarioFin": horarioFin,
                          "avatar": avatar, "listaDeProductos": listaDeProductos, "activo": activo, "formasDePago": formasDePago, "favoritos": favoritos}
            url = 'main/editar-vendedor-fijo.html'
        elif (tipo == 3):
            argumentos = {"nombre": nombre, "tipo": tipo, "id": id, "avatar": avatar, "listaDeProductos": listaDeProductos,
                  "activo": activo, "formasDePago": formasDePago, "favoritos": favoritos}
            url = 'main/editar-vendedor-ambulante.html'
        return render(request, url, argumentos)
    else:
        return render(request, 'main/index.html', {})


@csrf_exempt
def editarDatos(request):
    id_vendedor = request.POST.get("id_vendedor")
    usuario = get_object_or_404(User, id=id_vendedor)
    cliente = get_object_or_404(Cliente, user = usuario)
    nombre = request.POST.get("nombre")
    tipo = request.POST.get("tipo")

    if (tipo == "2"):
        horaInicial = request.POST.get("horaIni")
        horaFinal = request.POST.get("horaFin")
        print(tipo, horaInicial, horaFinal)
        if (not(horaInicial is None)):
            cliente.horarioIni = horaInicial
        if (not(horaFinal is None)):
            cliente.horarioFin = horaFinal
            # actualizar vendedores fijos
        for p in Cliente.objects.all():
            if p.tipo == 2:
                hi = p.horarioIni
                hf = p.horarioFin
                horai = hi[:2]
                horaf = hf[:2]
                mini = hi[3:5]
                minf = hf[3:5]
                print(datetime.datetime.now().time())
                tiempo = str(datetime.datetime.now().time())
                print(tiempo)
                hora = tiempo[:2]
                minutos = tiempo[3:5]
                estado = ""
                tiempo = str(datetime.datetime.now().time())
                print(tiempo)
                hora = tiempo[:2]
                minutos = tiempo[3:5]
                estado = ""
                if horaf >= hora and hora >= horai:
                    if horai == hora:
                        if minf >= minutos and minutos >= mini:
                            estado = "activo"
                        else:
                            estado = "inactivo"
                    elif horaf == hora:
                        if minf >= minutos and minutos >= mini:
                            estado = "activo"
                        else:
                            estado = "inactivo"
                    else:
                        estado = "activo"
                else:
                    estado = "inactivo"
                if estado == "activo":
                    Cliente.objects.filter(user=p).update(activo=1)
                else:
                    Cliente.objects.filter(user=p).update(activo=0)
    avatar = request.FILES.get("avatar")
    formasDePago = ""
    if not (request.POST.get("formaDePago0") is None) and request.POST.get("formaDePago0")!="":
        formasDePago += '0,'
    if not (request.POST.get("formaDePago1") is None) and request.POST.get("formaDePago1")!="":
        formasDePago += '1,'
    if not (request.POST.get("formaDePago2") is None) and request.POST.get("formaDePago2")!="":
        formasDePago += '2,'
    if not (request.POST.get("formaDePago3") is None) and request.POST.get("formaDePago3")!="":
        formasDePago += '3,'

    if (nombre is not None and nombre!=""):
        usuario.username = nombre
        
    if (formasDePago != ""):
        cliente.formasDePago = formasDePago[:-1]

    if (avatar is not None and avatar!=""):
        with default_storage.open('../media/avatars/' + str(avatar), 'wb+') as destination:
            for chunk in avatar.chunks():
                destination.write(chunk)
        cliente.avatar ='/avatars/'+ str(avatar)
    usuario.save()
    cliente.save()
    request.session['nombre'] = nombre
    return redirect('index')

def inicioAlumno(request):
    id = request.session['id']
    vendedores =[]
    # si son vendedores, crear lista de productos
    for p in Cliente.objects.all():
        if p.user.id == id:
            avatar = p.avatar
        if p.tipo == 2 or p.tipo == 3:
            vendedores.append(p.user.id)
    vendedoresJson = simplejson.dumps(vendedores)
    return render(request, 'main/index.html',{"id": id,"vendedores": vendedoresJson,"avatarSesion": avatar, "nombresesion": request.session['nombre']})

@csrf_exempt
def borrarProducto(request):
    if request.method == 'GET':
        if request.is_ajax():
            comida = request.GET.get('eliminar')
            Comida.objects.filter(nombre=comida).delete()
            data = {"eliminar" : comida}
            return JsonResponse(data)

@csrf_exempt
def editarProducto(request):
    if request.method == 'POST':
        if request.is_ajax():
            form = editarProductosForm(data=request.POST, files=request.FILES)
            print(request.POST)
            print(request.FILES)
            nombreOriginal = request.POST.get("nombreOriginal")
            nuevoNombre = request.POST.get('nombre')
            nuevoPrecio = (request.POST.get('precio'))
            nuevoStock = (request.POST.get('stock'))
            nuevaDescripcion = request.POST.get('descripcion')
            nuevaCategoria = (request.POST.get('categoria'))
            nuevaImagen = request.FILES.get("comida")
            if nuevoPrecio != "" :
                   Comida.objects.filter(nombre=nombreOriginal).update(precio=int(nuevoPrecio))
            if nuevoStock != "" :
                   Comida.objects.filter(nombre=nombreOriginal).update(stock=int(nuevoStock))
            if nuevaDescripcion != "":
                   Comida.objects.filter(nombre=nombreOriginal).update(descripcion=nuevaDescripcion)
            if  nuevaCategoria != None:
                   Comida.objects.filter(nombre=nombreOriginal).update(categorias=(nuevaCategoria))
            if nuevaImagen != None:
                filename = nombreOriginal + ".jpg"
                with default_storage.open('../media/productos/' + filename, 'wb+') as destination:
                    for chunk in nuevaImagen.chunks():
                        destination.write(chunk)
                Comida.objects.filter(nombre =nombreOriginal).update(imagen='/productos/'+filename)

            if nuevoNombre != "":
                if Comida.objects.filter(nombre=nuevoNombre).exists():
                    data = {"respuesta": "repetido"}
                    return JsonResponse(data)
                else:
                    Comida.objects.filter(nombre=nombreOriginal).update(nombre=nuevoNombre)

            data = {"respuesta" : nombreOriginal}
            return JsonResponse(data)

def cambiarFavorito(request):

    alumno = get_object_or_404(User, id=request.session['id'])

    
    if request.method == "GET":
        if request.is_ajax():
            favorito = request.GET.get('favorito')
            agregar = request.GET.get('agregar')
            
            print(favorito)
            vendedor = get_object_or_404(User, username=favorito)
            
            if agregar == "si":
                

                alumno.cliente.favoritos.add(vendedor.cliente)
                
                vendedor.cliente.favoritos.add(alumno.cliente)
                
                alumno.cliente.save()
                vendedor.cliente.save()


                
                
                respuesta = {"respuesta": "si"}
            else:
                alumno.cliente.favoritos.remove(vendedor.cliente)
                vendedor.cliente.favoritos.remove(alumno.cliente)
                alumno.cliente.save()
                vendedor.cliente.save()
                respuesta = {"respuesta": "no"}
            return JsonResponse(respuesta)

    #return render_to_response('main/baseAdmin.html', {'form':form,'test':test}, context_instance=RequestContext(request))


def cambiarEstado(request):

    usuario = get_object_or_404(User, id=request.session['id'])

    if request.method == 'GET':
        if request.is_ajax():
            estado = request.GET.get('estado')
            id_vendedor = request.GET.get('id')
            if estado == "true":
                usuario.cliente.activo = True
            else:
                usuario.cliente.activo = False
            data = {"estado": estado}
            usuario.cliente.save()
            return JsonResponse(data)


def editarPerfilAlumno(request):
    avatar = request.session['avatar']
    id = request.session['id']
    nombre =request.session['nombre']
    favoritos =[]
    nombres = []
    usuario = get_object_or_404(User, id=id)

    for fav in usuario.cliente.favoritos.all():
        
        favoritos.append(fav.user.id)
        vendedor = get_object_or_404(User, id=fav.user.id)
        nombre = vendedor.username
        nombres.append(nombre)
    return render(request,'main/editar-perfil-alumno.html',{"id": id, "avatarSesion": avatar,"nombre": nombre,"favoritos": favoritos, "nombres": nombres, "nombresesion":request.session['nombre']})


def procesarPerfilAlumno(request):
    if request.method == "POST":
        nombreOriginal = request.session['id']
        nuevoNombre = request.POST.get("nombre")
        count = request.POST.get("switchs")
        aEliminar= []
        nuevaImagen = request.FILES.get("comida")
        for i in range(int(count)):
            fav = request.POST.get("switch"+str(i))
            if fav != "":
                aEliminar.append(fav)
        print(request.POST)
        print(request.FILES)
        print(aEliminar)

        usuario = get_object_or_404(User, id=nombreOriginal)
        if nuevoNombre != "":
            if User.objects.filter(username=nuevoNombre).exists():
                data = {"respuesta": "repetido"}
                return JsonResponse(data)
            usuario.username = nuevoNombre



        for i in aEliminar:
            print("hola")

            vendedor = get_object_or_404(User, id=i)
            print("chao")
                

            usuario.cliente.favoritos.remove(vendedor.cliente)
                
            vendedor.cliente.favoritos.remove(usuario.cliente)
                
                
            vendedor.cliente.save()
            
        if nuevaImagen != None:
            filename = nombreOriginal + ".jpg"
            with default_storage.open('../media/avatars/' + filename, 'wb+') as destination:
                for chunk in nuevaImagen.chunks():
                    destination.write(chunk)
            usuario.client.avatar= ('/avatars/' + filename)

        usuario.save()
        usuario.cliente.save()

        return JsonResponse({"ejemplo": "correcto"})


@csrf_exempt
def borrarUsuario(request):
    if request.method == 'GET':
        if request.is_ajax():
            uID = request.GET.get('eliminar')
            Cliente.objects.filter(id=uID).delete()
            data = {"eliminar" : uID}
            return JsonResponse(data)

@csrf_exempt
def agregarAvatar(request):
    if request.is_ajax() or request.method == 'FILES':
        imagen = request.FILES.get("image")
        print(request.FILES)
        nuevaImagen = Imagen(imagen=imagen)
        nuevaImagen.save()
        return HttpResponse("Success")


def editarUsuarioAdmin(request):
    if request.method == 'GET':
            nombre = request.GET.get("name")
            contraseña = request.GET.get('password')
            email = request.GET.get('email')
            avatar = request.GET.get('avatar')
            userID = request.GET.get('userID')

            if  (nombre!=None):
                print ("nombre:"+nombre)
            if (contraseña != None):
                print ("contraseña:"+contraseña)
            if (email != None):
                print ("email:"+email)
            if (avatar != None):
                print ("avatar:"+avatar)
            if (userID != None):
                print("id:"+userID)
            if email != None:
                Cliente.objects.filter(id=userID).update(email=email)
                print("cambio Mail")
            if nombre != None:
                Cliente.objects.filter(id=userID).update(nombre=nombre)
                print("cambio Nombre")
            if contraseña != None:
                Cliente.objects.filter(id=userID).update(contraseña=contraseña)
                print("cambio contraseña")
            if avatar != None:
                Cliente.objects.filter(id=userID).update(avatar=avatar)
                print("cambio avatar")

            data = {"respuesta": userID}
            return JsonResponse(data)


def editarUsuario(request):
    if request.method == 'GET':

            nombre = request.GET.get("name")
            contraseña = request.GET.get('password')
            tipo = request.GET.get('type')
            email = request.GET.get('email')
            avatar = request.GET.get('avatar')
            forma0 = request.GET.get('forma0')
            forma1 = request.GET.get('forma1')
            forma2 = request.GET.get('forma2')
            forma3 = request.GET.get('forma3')
            horaIni = request.GET.get('horaIni')
            horaFin = request.GET.get('horaFin')
            userID = request.GET.get('userID')

            nuevaListaFormasDePago = ""
            if(nombre!=None):
                print ("nombre:"+nombre)
            if (contraseña != None):
                print ("contraseña:"+contraseña)
            if (tipo != None):
                print ("tipo:"+tipo)
            if (email != None):
                print ("email:"+email)
            if (avatar != None):
                print ("avatar:"+avatar)
            if (horaIni != None):
                print("horaIni:"+horaIni)
            if (horaFin != None):
                print("horaFin:" + horaFin)
            if (userID != None):
                print("id:"+userID)
            if (forma0 != None):
                print("forma0:" + forma0)
                nuevaListaFormasDePago+="0"
            if (forma1 != None):
                print("forma1:" + forma1)
                if(len(nuevaListaFormasDePago)!=0):
                    nuevaListaFormasDePago += ",1"
                else:
                    nuevaListaFormasDePago += "1"
            if (forma2 != None):
                print("forma2:" + forma2)
                if (len(nuevaListaFormasDePago) != 0):
                    nuevaListaFormasDePago += ",2"
                else:
                    nuevaListaFormasDePago += "2"
            if (forma3 != None):
                print("forma3:" + forma3)
                if (len(nuevaListaFormasDePago) != 0):
                    nuevaListaFormasDePago += ",3"
                else:
                    nuevaListaFormasDePago += "3"


            litaFormasDePago = (
                (0, 'Efectivo'),
                (1, 'Tarjeta de Crédito'),
                (2, 'Tarjeta de Débito'),
                (3, 'Tarjeta Junaeb'),
            )
            if email != None:
                Cliente.objects.filter(id=userID).update(email=email)
                print("cambio Mail")
            if nombre != None:
                Cliente.objects.filter(id=userID).update(nombre=nombre)
                print("cambio Nombre")
            if contraseña != None:
                Cliente.objects.filter(id=userID).update(contraseña=contraseña)
                print("cambio contraseña")
            if tipo != None:
                Cliente.objects.filter(id=userID).update(tipo=tipo)
                print("cambio tipo")
            if avatar != None:
                Cliente.objects.filter(id=userID).update(avatar=avatar)
                print("cambio avatar")
            if horaIni != None:
                Cliente.objects.filter(id=userID).update(horarioIni=horaIni)
                print("cambio hora ini")
            if horaFin != None:
                Cliente.objects.filter(id=userID).update(horarioFin=horaFin)
                print("cambio hora fin")
            Cliente.objects.filter(id=userID).update(formasDePago=nuevaListaFormasDePago)
            print("cambio formas de pago")

            data = {"respuesta" : userID}
            return JsonResponse(data)

def registerAdmin(request):
    tipo = 0
    nombre = request.POST.get("nombre")
    email = request.POST.get("email")
    password = request.POST.get("password")
    horaInicial = request.POST.get("horaIni")
    horaFinal = request.POST.get("horaFin")
    avatar = request.FILES.get("avatar")
    #print(avatar)
    formasDePago = []
    if not (request.POST.get("formaDePago0") is None):
        formasDePago.append(request.POST.get("formaDePago0"))
    if not (request.POST.get("formaDePago1") is None):
        formasDePago.append(request.POST.get("formaDePago1"))
    if not (request.POST.get("formaDePago2") is None):
        formasDePago.append(request.POST.get("formaDePago2"))
    if not (request.POST.get("formaDePago3") is None):
        formasDePago.append(request.POST.get("formaDePago3"))


    usuario, created = User.objects.get_or_create(username=nombre,email = email)

    if(created):
        usuario.set_password(password)

    usuarioNuevo = Cliente(user=usuario, tipo=tipo, avatar=avatar,
                               formasDePago=formasDePago, horarioIni=horaInicial, horarioFin=horaFinal)
    usuarioNuevo.save()
    
    return loginReq(request)

@csrf_exempt
def verificarEmail(request):
    if request.is_ajax() or request.method == 'POST':
        email = request.POST.get("email")
        print(email)
        if User.objects.filter(email=email).exists():
            data = {"respuesta": "repetido"}
            return JsonResponse(data)
        else:
            data = {"respuesta": "disponible"}
            return JsonResponse(data)

def getStock(request):
    if request.method == "GET":
        stock = request.GET.get("nombre")
        for producto in Comida.objects.raw("SELECT * FROM Comida"):
            if producto.nombre == request.GET.get("nombre"):
                stock =  producto.stock
        if request.GET.get("op") == "suma":
            nuevoStock = stock + 1
            Comida.objects.filter(nombre=request.GET.get("nombre")).update(stock=nuevoStock)
        if request.GET.get("op") == "resta":
            nuevoStock = stock - 1
            if stock == 0:
                return JsonResponse({"stock": stock})
            Comida.objects.filter(nombre=request.GET.get("nombre")).update(stock=nuevoStock)
    return JsonResponse({"stock": stock})

def createTransaction(request):
    print("GET:")
    print(request.GET)
    nombreProducto = request.GET.get("nombre")
    precio=0
    idVendedor = request.GET.get("idUsuario")
    if Comida.objects.filter(nombre=nombreProducto).exists():
        precio = Comida.objects.filter(nombre=nombreProducto).values('precio')[0]
        listaAux=list(precio.values())
        precio=listaAux[0]
        print(precio)
    else:
        return HttpResponse('error message')
    print(nombreProducto)
    transaccionNueva = Transacciones(idVendedor=idVendedor,precio=precio,nombreComida=nombreProducto)
    transaccionNueva.save()
    return JsonResponse({"transaccion": "realizada"})


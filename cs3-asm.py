'''
Ensamblador para el computador 
académico Computador Simple 3

Desarrollado por Francisco Sánchez López 
bajo la licencia GNU Public License v3

2018 - Universad de Sevilla

Versión 1.0b
'''

import sys,json

#alias de registros
regs = {}
try:
	with open("regs.json","r") as regs_f:
		regs = json.load(regs_f)
except IOError as e:
	print("Error al abrir el diccionario de registros!")
	print(e)
	exit(1)

error_ensamblando = False

#recibe la ruta de un archivo y devuelve una lista con las lineas formateadas
def leer_archivo(ruta):
	lineas = []

	try:
		with open(ruta) as f:
			lineas = [formatear_texto(linea) for linea in f]
	except IOError as e:
		print("Error al abrir el archivo!")
		print(e)
		exit(1)
	return lineas
	
def coger_lineas(ruta):
	salida = []
	contador_lineas = 0
	for linea in leer_archivo(ruta):
		if linea != None:
			if linea[0] != '.equ':
				if linea[0] == '.include':
					salida+=coger_lineas(linea[1])
				else:
					if linea[0][-1] == ':':
						salida.append(linea[1:])
					else:
						salida.append(linea)
	return salida
	
#comprueba que el dato es valido para el computador y lo pasa a bin desde dec o hex
#si no es valido, devuelve None. El valor no puede se mayor que 0xff,256 o 0b1111111
def formatear_valor(num,archivo,entrada):
	salida = None
	
	entrada = str(entrada)
	
	#es binario el dato
	if entrada[:2] == "0b":
		cerouno = True
		for e in entrada[2:0]:
			if not (e == '0' or e == '1'):
				cerouno = False
		if cerouno:
			if len(entrada[2:].lstrip('0')) <= 8:
				salida = entrada[2:].rjust(8,'0')
			else:
				mostrar_error(num,archivo,"El valor -" + entrada + "- tiene más de 8 bits")
		else:
			mostrar_error(num,archivo,"El valor -" + entrada + "- no es binario")
			
	#es hex el dato
	elif entrada[:2] == "0x":
		if len(entrada[2:].lstrip('0')) <= 2:
			#vemos que son numeros hex del 0 a la f
			if entrada[2:].isalnum():
				salida = bin(int(entrada[2:],16))[2:].rjust(8,'0')
			else:
				mostrar_error(num,archivo,"El valor -" + entrada + "- no es hexadecimal")
		else:
			mostrar_error(num,archivo,"El valor -" + entrada + "- es mayor que 0xFF")
	#si no, pues decimal
	else:
		if entrada.isdecimal() or (entrada[1:].isdecimal() and entrada[0] == '-'):
			valor = int(entrada)
			if valor <= 255:
				if valor >= 0:
					salida = bin(int(entrada))[2:].rjust(8,'0')
				else:
					#si es negativo le hacemos el ca2
					if valor >= -128:
						salida = bin(256-abs(int(entrada)))[2:]
					else:
						mostrar_error(num,archivo,"El valor -" + entrada + "- es menor de lo permitido")
			else:
				mostrar_error(num,archivo,"El valor -" + entrada + "- es mayor de lo permitido")
		else:
			mostrar_error(num,archivo,"El valor -" + entrada + "- no es decimal")
			
			
	return salida

#tipo de organizacion de bits de unas instrucciones
def func1_ins(num,archivo,macros,entrada):
	salida = ""
	#si hay argumentos
	if len(entrada) == 1:
		reg = entrada[0].split(",")
		
		#que haya dos registros separados por comas
		if len(reg) == 2:
			#si se han definido en una macro
			reg[0] = macros.get(reg[0],reg[0])
			reg[1] = macros.get(reg[1],reg[1])
			
			#que sean registros
			if reg[0] in regs and reg[1] in regs:
				salida +=regs[reg[0]] + "00000" + regs[reg[1]]
			else:
				mostrar_error(num,archivo,"Los registros no están bien escritos")
		else:
			mostrar_error(num,archivo,"Hay problemas con los argumentos")
	else:
		mostrar_error(num,archivo,"Faltan argumentos")
		
	return salida
	
#un tipo de instruccion, muy parecida a lds
def sts_ins(num,archivo,macros,entrada):
	salida = "00010"
	#que haya argumentos
	if len(entrada) == 1:
		reg = entrada[0].split(",")
		
		#que cada argumento este separado por comas
		if len(reg) == 2:
			reg[0] = formatear_valor(num,archivo,macros.get(reg[0],reg[0]))
			reg[1] = macros.get(reg[1],reg[1])
			
			#que sean correctos
			if reg[0] != None and reg[1] in regs:
				salida+=regs[reg[1]] + reg[0]
			else:
				mostrar_error(num,archivo,"Los registros no están bien escritos")
		else:
			mostrar_error(num,archivo,"Hay problemas con los argumentos")
	else:
		mostrar_error(num,archivo,"Faltan argumentos")
		
	return salida
	
def lds_ins(num,archivo,macros,entrada):
	salida = "00011"
	if len(entrada) > 0:
		reg = entrada[0].split(",")
		
		if len(reg) == 2:
			reg[0] = macros.get(reg[0],reg[0])
			reg[1] = formatear_valor(num,archivo,macros.get(reg[1],reg[1]))
			
			if reg[1] != None and reg[0] in regs:
				salida+=regs[reg[0]] + reg[1]
			else:
				mostrar_error(num,archivo,"Los registros no están bien escritos")
		else:
			mostrar_error(num,archivo,"Hay problemas con los argumentos")
	else:
		mostrar_error(num,archivo,"Faltan argumentos")
		
	return salida
	
def func3_ins(num,archivo,etiquetas,entrada):
	salida = ""
	if len(entrada) == 1:
		salto = formatear_valor(num,archivo,etiquetas.get(entrada[0],entrada[0]))
		if salto != None:
			salida+=salto
		else:
			mostrar_error("La dirección de salto no es correcta")
	else:
		mostrar_error(num,archivo,"Hay problemas con los argumentos")
		
	return salida
	
#esta instruccion tiene una peculiaridad, ya que depende del nemonico
def br_ins(num,archivo,etiquetas,entrada):
	salida = '00110'
	if len(entrada) == 2:
		if entrada[0][2:] == "zs":
			salida+="000"
		elif entrada[0][2:] == "eq":
			salida+="000"
		elif entrada[0][2:] == "cs":
			salida+="001"
		elif entrada[0][2:] == "lo":
			salida+="001"
		elif entrada[0][2:] == "vs":
			salida+="010"
		elif entrada[0][2:] == "lt":
			salida+="011"
		else:
			mostrar_error(num,archivo,"La instrucción no está bien escrita")
		
		salto = formatear_valor(num,archivo,etiquetas.get(entrada[1],entrada[1]))
		if salto != None:
			salida+=salto
		else:
			mostrar_error(num,archivo,"La dirección de salto no es correcta")
		
	else:
		mostrar_error(num,archivo,"Hay problemas con los argumentos")
		
	return salida
	
def func2_ins(num,archivo,macros,entrada):
	salida = ""
	if len(entrada) == 1:
		reg = entrada.split(",")
		if len(regs) == 2:
			reg[0] = macros.get(reg[0],reg[0])
			reg[1] = formatear_valor(num,archivo,macros.get(reg[1],reg[1]))
			
			if reg[0] in regs and reg[1] != None:
				salida +=reg[0] + reg[1]
			else:
				mostrar_error(num,archivo,"Los registros no están bien escritos")
		else:
			mostrar_error(num,archivo,"Hay problemas con los argumentos")
	else:
		mostrar_error(num,archivo,"Faltan argumentos")
		
	return salida
	
#se encarga de juntar las etiquetas y las macros en las operaciones, es recursiva sobre si misma
def ensamblar(macros,etiquetas,ruta):
	salida = []
	
	#contador de las lineas de codigo
	contador = 1
	for linea in leer_archivo(ruta):
		if linea is not None:
			#quitamos las etiquetas
			if linea[0][-1] == ':':
				linea = linea[1:]
		
			#buscamos macros
			if linea[0] in macros:
				linea = formatear_texto(macros[linea[0]])
		
			#y buscamos por cada ins, algunas ins tienen funcion propia
			if linea[0] == 'st':
				salida.append("00001" + func1_ins(contador,ruta,macros,linea[1:]))
			elif linea[0] == 'ld':
				salida.append("00000" + func1_ins(contador,ruta,macros,linea[1:]))
			elif linea[0] == 'sts':
				salida.append(sts_ins(contador,ruta,macros,linea[1:]))
			elif linea[0] == 'lds':
				salida.append(lds_ins(contador,ruta,macros,linea[1:]))
			elif linea[0] == 'call':
				salida.append("00100000" + func3_ins(contador,ruta,etiquetas,linea[1:]))
			elif linea[0] == 'ret':
				salida.append("0010100000000000")
			elif linea[0][:2] == 'br':
				salida.append(br_ins(contador,ruta,etiquetas,linea))
			elif linea[0] == 'jmp':
				salida.append("00111000" + func3_ins(contador,ruta,etiquetas,linea[1:]))
			elif linea[0] == 'add':
				salida.append("01000" + func1_ins(contador,ruta,macros,linea[1:]))
			elif linea[0] == 'sub':
				salida.append("01010" + func1_ins(contador,ruta,macros,linea[1:]))
			elif linea[0] == 'cp':
				salida.append("01011" + func1_ins(contador,ruta,macros,linea[1:]))
			elif linea[0] == 'mov':
				salida.append("01111" + func1_ins(contador,ruta,macros,linea[1:]))
			elif linea[0] == 'stop':
				salida.append("1011100000000000")
			elif linea[0] == 'subi':
				salida.append("11010" + func2_ins(contador,ruta,macros,linea[1:]))
			elif linea[0] == 'cpi':
				salida.append("11011" + func2_ins(contador,ruta,macros,linea[1:]))
			elif linea[0] == 'ldi':
				salida.append("11111" + func2_ins(contador,ruta,macros,linea[1:]))
			elif linea[0] == '.equ':
				True
			elif linea[0] == '.include':
				salida+=ensamblar(macros,etiquetas,linea[1])
			else:
				mostrar_error(contador,ruta,"La instrucción -" + linea[0] + "- no está bien escrita")
		contador +=1
	
	return salida
	
'''
Esta función procesa las macros y las etiquetas. Recibe de parametro
la ruta del archivo y un offset para las etiquetas
'''
def procesar(ruta,offset=0):
	macros = {}
	etiquetas = {}
	
	lineas = leer_archivo(ruta)
	for i in range(len(lineas)):
		if lineas[i] != None:
			
			linea = lineas[i]
			#si es una macro
			if linea[0] == ".equ":
				#que haga referncia a algo
				if len(linea) > 1:
					#queremos splitear segun '=' no segun ' ', reordenamos la frase
					nueva_linea = ""
					for palabra in linea[1:]:
						nueva_linea+=palabra + " "
						
					args = nueva_linea.split("=")
					
					args[0] = args[0].strip()
					
					#esto se hace por si hay mas de un '=', para que solo se tenga en cuenta el primero
					dest = ""
					for palabra in args[1:]:
						dest+=palabra
					dest = dest.strip()
					
					if len(args) == 2:
						if args[0] in macros:
							mostrar_error(i+1,archivo,"Macro duplicada")
						else:
							macros[args[0]] = dest
					else:
						mostrar_error(i+1,archivo,"Problema con los argumentos")
				else:
					mostrar_error(i+1,archivo,"Problema con los argumentos")
					
			#esto si es una etiqueta		
			elif linea[0][-1] == ':':
				if len(linea) > 1:
					etiqueta = linea[0][:-1]
					if etiqueta in etiquetas:
						mostrar_error(i+1,archivo,"Etiqueta duplicada")
					else:
						etiquetas[etiqueta] = int(offset)
					offset += 1
				else:
					mostrar_error(i+1,archivo,"Etiqueta a nada")	
			elif linea[0] == '.include':
				if len(linea) == 2:
					result = procesar(linea[1],offset)
					macros.update(result[0])
					etiquetas.update(result[1])
					offset = result[2]
				else:
					mostrar_error(i+1,archivo,".include mal formulado")
			else:
				offset += 1

	return (macros,etiquetas,offset)
						

def ensamblar_principal(origen,destino):
	result = procesar(origen)
	macros = result[0]
	etiquetas = result[1]
	
	if error_ensamblando:
		print("Hubo errores de ensamblaje")
		exit(1)
	
	final = ensamblar(macros,etiquetas,origen)	
	
	if error_ensamblando:
		print("Hubo errores de ensamblaje")
		exit(1)
	else:
		try:
			with open(destino,"w") as obj_f:
				for linea in final:
					obj_f.write(linea + "\n")
			print("Ensamblaje sin errores")
		except IOError as e:
			print("Error al escribir el archivo de destino!")
			print(e)
			exit(1)
		
'''
esta función nos coje una linea de código, devuelve una lista de
palabras, eliminando comentarios, espacios y tabulaciones. Si la
linea solo es comentario o esta vacía devuelve un None.
'''
def formatear_texto(entrada):
	#sustituir \t por espacios y separar palabras
	salida = entrada.expandtabs().split(" ")
	#quitar saltos de linea
	salida = [temp.rstrip("\n") for temp in salida]
	#ver que no hay ningua entrada nula
	salida = [temp for temp in salida if temp is not ""]
	
	salida_final = []
	#eliminamos los comentarios y ponemos todo en minusculas
	for palabra in salida:
		if palabra[0] == ';':
			break
		elif palabra != '':
			salida_final.append(palabra.lower())
	
	#esto es para que no nos queden lineas vacias
	if len(salida_final) == 0:
		salida_final = None
		
	return salida_final
	
#funcion simple que nos imprime un error
def mostrar_error(num,archivo = " ",msg = ""):
	global error_ensamblando
	error_ensamblando = True
	print("Error línea " + str(num) + "," + archivo + ": " + msg)

def ayuda():
	print("Mensaje de ayuda del ensamblador del Computador Simple 3 \n\nSintaxis: python " + sys.argv[0] + " -v $entrada $salida")
	print("Opciones: \n\t -v : se muestran detalles del ensamblaje.")
	
def main():
	if len(sys.argv) == 3:
		ensamblar_principal(sys.argv[1],sys.argv[2])
	else:
		print("**Problema con los argumentos**\n")
		ayuda()
				
main()

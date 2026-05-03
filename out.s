	
.section	.data
	.align 8
x: .long 0
squ: .long 0
.section	.text
	.align
	.global main
	.type main, %function

	
main : push {lr}
	mov r0, #1
	ldr r12, =x
	str r0, [r12]
label2 : ldr r12, =x
	ldr r2, [r12]
	mov r0, #10
	cmp r2, r0
	bgt label1
	
	bl square
	ldr r12, =x
	ldr r1, [r12]
	mov r0, #1
	add r0, r1, r0
	ldr r12, =x
	str r0, [r12]
	push {r0}
	ldr r12, =squ
	ldr r0, [r12]
	bl print
	pop {r0}
	b label2
label1 : 
	pop {pc}
	
	
	.global square
	.type square, %function
square: 
	
	push {lr}
	

	
	ldr r12, =x
	ldr r1, [r12]
	ldr r12, =x
	ldr r0, [r12]
	mul r0, r1, r0
	ldr r12, =squ
	str r0, [r12]
	
	pop {pc}

#include <stdint.h>
#include <stddef.h>

extern char uart_get();
extern void uart_send(unsigned int c);

int mystrlen(char *data) {
    int i=0;
    while(1) {
        if(data[i++] == '\0'){
            break;
        }
    }
    return i-1;
}

#define DEBUGGER_SHARED_GLOBALS 0x100000
#define DEBUGGER_LOAD_ADDRESS DEBUGGER_SHARED_GLOBALS + 0x1000
// #define DEBUGGER_SEND_DATA DEBUGGER_SHARED_GLOBALS + 0
// #define DEBUGGER_RECV_DATA DEBUGGER_SHARED_GLOBALS + 8
// TODO fix this
#define DEBUGGER_SEND_DATA 0x0000000000080050 
#define DEBUGGER_RECV_DATA 0x0000000000080084

void recv_data(void *address, uint32_t size){
    for(int i=0; i < size; i++){
        *((char *)address + i) = uart_get();
    }
}

void send(void *address, uint64_t size, uint32_t *error){
    for(int i=0; i < size; i++){
        uart_send(*((char *)address + i));
    }
    // Read the address of the function from the shared memory
    // void (*custom_func)(void *address, uint64_t size) = (void *)DEBUGGER_SEND_DATA; 
    // custom_func(address, size);
}

void usb_log(char * msg, uint32_t * error){
	send(msg, mystrlen(msg), error);    
}

void concrete_main(uint64_t debugger){

}
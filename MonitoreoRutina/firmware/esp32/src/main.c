
#include <stdio.h>
#include <inttypes.h>

#include "esp_system.h"
#include "esp_timer.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

void app_main(void)
{
    printf("\n");
    printf("Sistema domotico iniciado\n");
    printf("ESP-IDF: %s\n", esp_get_idf_version());

    while (1)
    {
        int64_t timestamp = esp_timer_get_time();

        printf("Uptime: %" PRId64 " us\n", timestamp);

        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

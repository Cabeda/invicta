import {defineConfig} from '@playwright/test';
export default defineConfig({
  testDir:'./tests/browser',workers:1,timeout:90_000,expect:{timeout:30_000},
  use:{baseURL:'http://127.0.0.1:8767',viewport:{width:1360,height:1000},launchOptions:{args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']}},
  webServer:{command:'python3 -m http.server 8767 --bind 127.0.0.1 --directory prototypes/costa-cabral/proposal',url:'http://127.0.0.1:8767',reuseExistingServer:false,stdout:'ignore',stderr:'ignore'},
  reporter:'list'
});

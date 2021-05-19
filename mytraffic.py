import time
import random
from pyknow import *
exeTimes = 100  # time in second


class MyTrafficLights(KnowledgeEngine):
    """
    分为三个部分：
    1.时间增加：等级1
    2.变更红灯：等级2
    3.在周期结束时更新亮灯时间比值，等级2
    注： 展示灯为等级3，切换了之后再展示
    """
    @DefFacts()
    def _initial_action(self):
        yield Fact(Ticks=0.0)  # 时钟计数
        yield Fact(NSLight="YELLOW")  # 南北灯
        yield Fact(EWLight="RED")  # 东西灯
        yield Fact(NSRed2GreenTick=5.0)  # 南北灯红灯基准持续时间
        yield Fact(NSGren2YellowTick=4.0)  # 南北绿灯基准持续时间
        yield Fact(NSYello2RedTick=1)  # 南北黄灯基准持续时间
        yield Fact(Period=10.0)  # 一次红绿黄等全走完的时间周期
        yield Fact(NSExess=1.0)  # 南北绿灯相较于绿灯基准时间的倍数
        yield Fact(NSCars=1)  # 南北车通过的数量
        yield Fact(WECars=1)  # 东西车通过的数量
        yield Fact(ChangeLights=False)  # 是否有切换灯的信号

    @Rule(AS.oldFact << Fact(Ticks=MATCH.times),
        salience=4
          )
    def ticks(self, times, oldFact):
        """
        时钟增加0.01s
        控制每个时间更新时输出现在的情况和退出
        """
        self.retract(oldFact)  # 删除旧的事实
        times += 1
        self.declare(Fact(Ticks=times))  # 增加0.01s
        time.sleep(0.01)
        if(times == exeTimes):
            print("BYE!")
        if(int(times*100) % 10 == 0):  # 每个0.01秒出一次时间
            print("{:.2f}s-*-".format(times))

    # # 在每个时间更新后，更新car,即0.01s记录一次车
    # @Rule(
    #     Fact(Ticks=MATCH.times),
    #     AS.fact1 << Fact(NSCars=MATCH.nsCars),
    #     AS.fact2 << Fact(WECars=MATCH.weCars),
    #     salience=1
    # )
    # def updateCars(self, fact1, fact2, nsCars, weCars):
    #     self.retract(fact1)
    #     self.retract(fact2)
    #     if random.randint(0, 5) == 0:
    #         self.declare(Fact(NSCars=nsCars+1))
    #     if random.randint(0, 5) == 0:
    #         self.declare(Fact(WECars=weCars+1))

    # # 在Period时计算新的Exess
    # @Rule(
    #     Fact(Ticks=MATCH.times),
    #     Fact(Period=MATCH.period),
    #     TEST(lambda times, period: int(times*100) %
    #          (period*100) == 0),  # 当时间为period整数倍
    #     AS.fact1 << Fact(NSCars=MATCH.nsCars),
    #     AS.fact2 << Fact(WECars=MATCH.weCars),
    #     AS.fact3 << Fact(SwitchTime=MATCH.nsExess),
    #     salience=2  # 优先级为2，优先级是指优先执行到,越低越先执行
    # )
    # def changeSwitchTime(self, period, fact1, fact2, fact3, nsCars, weCars, nsExess):
    #     # 删除旧的事实
    #     self.retract(fact1)
    #     self.retract(fact2)
    #     self.retract(fact3)
    #     # 保证分母不为0
    #     if nsCars == 0:
    #         nsCars = 1
    #     if weCars == 0:
    #         weCars = 1
    #     newnsExess = nsCars/(weCars+nsCars)  # 计算新的时间分配比例
    #     print('nsCars ={} and weCars={},so we changed switch NSEXess from {:.2f} to {:.2f}'.format(
    #         nsCars, weCars, nsExess, newnsExess))
    #     # 插入新的事实
    #     self.declare(Fact(NSCars=1))
    #     self.declare(Fact(WECars=1))
    #     self.declare(Fact(NSExess=newnsExess))

    # NS方向的红变绿
    @Rule(
        Fact(Ticks=MATCH.times),
        Fact(NSExess=MATCH.nsExess),
        Fact(Period=MATCH.period),
        Fact(NSRed2GreenTick=MATCH.nsRed2GreenTick),
        # 除以nsExess表示红灯时间变少 , 由于精确到0.01s，故乘100换算为整数
        TEST(lambda times, nsExess, period, nsRed2GreenTick: int(
            (times*100) % (period*100)) == int(nsRed2GreenTick/nsExess*100)),
        AS.fact2 << Fact(NSLight=MATCH.nsLight),
        TEST(lambda nsLight:nsLight == 'RED'),
        salience=2
    )
    def NSRed2Green(self, fact):
        self.retract(fact)
        self.declare(Fact(NSLight='GREEN'))

    # NS方向绿变黄
    @Rule(
        Fact(Ticks=MATCH.times),
        Fact(Period=MATCH.period),
        Fact(NSYello2RedTick=MATCH.nsYello2RedTick),
        # 绿灯时间为周期时间减后面的黄灯固定1s
        TEST(lambda times, period, nsYello2RedTick: int((times*100) %
                                                        (period*100)) == (period - nsYello2RedTick)*100),
        AS.fact << Fact(NSLight=MATCH.nsLight),
        TEST(lambda nsLight:nsLight == 'GREEN'),
        salience=2
    )
    def NSGreen2Yellow(self, fact):
        self.retract(fact)
        self.declare(Fact(NSLight='YELLOW'))

    # NS方向黄变红
    @Rule(
        Fact(Ticks=MATCH.times),
        Fact(Period=MATCH.period),
        # 当一个周期结束，就该回到一开始的红灯
        TEST(lambda times, period: int((times*100) % (period*100)) == 0),
        AS.fact << Fact(NSLight=MATCH.nsLight),
        TEST(lambda nsLight:nsLight == 'YELLOW'),
        salience=2
    )
    def NSYellow2Red(self, fact):
        self.retract(fact)
        self.declare(Fact(NSLight='RED'))

    # EW方向绿变黄
    @Rule(
        Fact(Ticks=MATCH.times),
        Fact(SwitchTime=MATCH.nsExess),
        Fact(Period=MATCH.period),
        Fact(NSRed2GreenTick=MATCH.nsRed2GreenTick),  # 需要用NS的标准时间换算
        TEST(lambda times, nsExess, period, nsRed2GreenTick: int(
            (times*100) % (period*100)) == int((nsRed2GreenTick/nsExess-1)*100)),
        AS.fact << Fact(EWLight=MATCH.ewLight),
        TEST(lambda ewLight:ewLight == 'GREEN'),
        salience=2
    )
    def EWGreen2Yellow(self, fact):
        self.retract(fact)
        self.declare(Fact(EWLight='YELLOW'))

    # EW方向黄变红
    @Rule(
        Fact(Ticks=MATCH.times),
        Fact(Period=MATCH.period),
        Fact(NSExess=MATCH.nsExess),
        Fact(NSRed2GreenTick=MATCH.nsRed2GreenTick),  # 需要用NS的标准时间换算
        TEST(lambda times, nsExess, period, nsRed2GreenTick: int(
            (times*100) % (period*100)) == int((nsRed2GreenTick/nsExess)*100)),
        AS.fact << Fact(EWLight=MATCH.ewLight),
        TEST(lambda ewLight:ewLight == 'YELLOW'),
        salience=2
    )
    def EWYellow2Red(self, fact):
        self.retract(fact)
        self.declare(Fact(EWLight='RED'))

    # EW方向红变绿
    @Rule(
        Fact(Ticks=MATCH.times),
        Fact(Period=MATCH.period),
        Fact(NSRed2GreenTick=MATCH.nsRed2GreenTick),  # 需要用NS的标准时间换算
        TEST(lambda times, period: int((times*100) % (period*100)) == 0),
        AS.fact << Fact(EWLight=MATCH.ewLight),
        Fact(EWLight='RED'),
        salience=2
    )
    def EWRed2Green(self, fact):
        self.retract(fact)
        self.declare(Fact(EWLight='GREEN'))

    @Rule(
        Fact(Ticks=MATCH.times),
        Fact(Period=MATCH.period),
        Fact(NSExess=MATCH.nsExess),
        Fact(NSRed2GreenTick=MATCH.nsRed2GreenTick),
        Fact(NSYello2RedTick=MATCH.nsYello2RedTick),
        TEST(lambda times, nsExess, period, nsRed2GreenTick,nsYello2RedTick:
            (int((times*100) % (period*100)) == int(nsRed2GreenTick/nsExess*100)) or # ns 红变绿 EW方向黄变红
            (int((times*100) % (period*100)) == (period - nsYello2RedTick)*100) or # ns 绿变黄
            (int((times*100) % (period*100)) == 0 )or   # ns 由绿->红，EW 由黄->绿
            (int((times*100) % (period*100)) == int((nsRed2GreenTick/nsExess-1)*100)) # EW方向绿变黄
        ),
        AS.fact << Fact(ChangeLights = False),
        salience=3
    )
    def isShow(self,fact):
        self.retract(fact)
        self.declare(Fact(ChangeLights=True))
    
    # 在各个变灯的时候亮灯
    @Rule(
        AS.fact << Fact(ChangeLights=MATCH.changeLights),
        TEST(lambda changeLights: changeLights == True),
        Fact(NSLight=MATCH.nsLight),
        Fact(EWLight=MATCH.ewLight),
        salience=3
    )
    def showLight(self, fact, nsLight, ewLight):
        self.retract(fact)
        ns = "R"
        if(nsLight == "GREEN"):
            ns = "G"
        elif(nsLight == "YELLOW"):
            ns = "Y"
        ew = 'R'
        if(ewLight == "GREEN"):
            ew = "G"
        elif(ewLight == "YELLOW"):
            ew = "Y"
        print('-{}-  -{}-'.format(ns, ew))

        self.declare(Fact(ChangeLights=False))


def main(args=None):
    engine = MyTrafficLights()
    engine.reset()
    engine.run()


if __name__ == "__main__":
    main()
